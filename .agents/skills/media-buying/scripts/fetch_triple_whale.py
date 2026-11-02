"""Liest tägliche Triple-Whale-Käufe und -Umsatz je Meta-Adset über den SQL-Endpunkt.

Nur lesend. Speichert die unveränderte Antwort unter <startup>/runden/YYYY-MM-DD/rohdaten/triple_whale.json.
Einstellungen (aktiv, Shop, Modell, Fenster, Kanal) aus <startup>/startup.json, Abschnitt "triple_whale".
Tabelle, Spalten, Modell- und Fensternamen sind beim ersten Lauf zu bestätigen (references/triple-whale-api.md).

    python fetch_triple_whale.py [--tag YYYY-MM-DD] [--tage 14] [--modell "..."] [--fenster ...]
"""
import argparse
import os
import re
from datetime import date, datetime, timedelta

from common import (FIXTURE, TEST_MODE, TW, TZ, http_json, now_iso, raw_dir, read_json, require_env,
                    require_real_data, write_json)

URL = "https://api.triplewhale.com/api/v2/orcabase/api/sql"
QUERY = """
SELECT event_date, adset_id, SUM(orders_quantity) AS purchases, SUM(order_revenue) AS revenue, SUM(spend) AS spend
FROM pixel_joined_tvf()
WHERE event_date BETWEEN @startDate AND @endDate
  AND channel = '{kanal}'
  AND model = '{model}'
  AND attribution_window = '{fenster}'
GROUP BY event_date, adset_id
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=datetime.now(TZ).date().isoformat())
    ap.add_argument("--tage", type=int, default=14)
    ap.add_argument("--modell", default=TW.get("modell"))
    ap.add_argument("--fenster", default=TW.get("fenster"))
    args = ap.parse_args()
    require_real_data()
    if not TW["aktiv"]:
        print("Triple Whale ist laut startup.json nicht aktiv; kein Abruf. Bericht zeigt nur Meta.")
        return
    kanal = TW.get("kanal") or "facebook-ads"
    for value in (args.modell, args.fenster, kanal):
        if not value or not re.fullmatch(r"[A-Za-z0-9 +_-]+", value):
            raise SystemExit(f"Unzulässiger oder fehlender Wert (startup.json, triple_whale): {value!r}")
    run_day = date.fromisoformat(args.tag)
    since = run_day - timedelta(days=args.tage)
    query = QUERY.format(model=args.modell, fenster=args.fenster, kanal=kanal)
    if TEST_MODE:
        shop, rows = "TESTDATEN", []
        for spec in read_json(FIXTURE)["konten"].values():
            for a in spec["adsets"]:
                for i, (buys, revenue, spend) in enumerate(a.get("tw") or []):
                    if buys or revenue or spend:
                        day = (run_day - timedelta(days=len(a["tw"]) - i)).isoformat()
                        rows.append({"event_date": day, "adset_id": a["id"], "purchases": buys,
                                     "revenue": revenue, "spend": spend})
        response = {"data": rows}
    else:
        key, = require_env("TRIPLEWHALE_API_KEY")
        shop = os.environ.get("TRIPLEWHALE_SHOP_DOMAIN") or TW.get("shop_domain")
        if not shop:
            raise SystemExit("Triple-Whale-Shop fehlt: startup.json triple_whale.shop_domain oder TRIPLEWHALE_SHOP_DOMAIN.")
        body = {"shopId": shop, "query": query,
                "period": {"startDate": since.isoformat(), "endDate": run_day.isoformat()}}
        response = http_json("POST", URL, body=body, headers={"x-api-key": key, "Accept": "application/json"})
    data = {"abgerufen": now_iso(), "shop": shop, "modell": args.modell, "fenster": args.fenster,
            "zeitraum": [since.isoformat(), run_day.isoformat()], "query": query, "antwort": response}
    path = write_json(raw_dir(run_day) / "triple_whale.json", data)
    rows = response if isinstance(response, list) else response.get("data") or response.get("rows") or []
    print(f"Triple Whale: {len(rows)} Zeilen -> {path}")


if __name__ == "__main__":
    main()
