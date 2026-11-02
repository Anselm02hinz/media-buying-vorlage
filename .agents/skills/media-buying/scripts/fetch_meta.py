"""Liest Konto, Adsets, tägliche Adset-Insights und Änderungsaktivitäten aus der Meta Marketing API.

Nur lesende GET-Aufrufe. Speichert die unveränderten Antworten (ohne Paging-URLs) unter
<startup>/runden/YYYY-MM-DD/rohdaten/meta_<konto>.json. Konten aus <startup>/startup.json.

    python fetch_meta.py [--tag YYYY-MM-DD] [--tage 14] [--konten <schlüssel> ...]
"""
import argparse
import json
import os
import re
import time
from datetime import date, datetime, timedelta

from common import (ACCOUNTS, FIXTURE, META_API_VERSION, TEST_MODE, TZ, ApiError, http_json, now_iso, raw_dir,
                    read_json, require_env, require_real_data, write_json)

ADSET_FIELDS = ("id,name,status,effective_status,daily_budget,lifetime_budget,budget_remaining,bid_strategy,"
                "start_time,end_time,created_time,updated_time,attribution_spec,"
                "campaign{id,name,status,effective_status,daily_budget,lifetime_budget,bid_strategy}")
ADSET_STATES = ["ACTIVE", "PAUSED", "ADSET_PAUSED", "CAMPAIGN_PAUSED", "IN_PROCESS", "WITH_ISSUES",
                "PENDING_REVIEW", "PREAPPROVED", "PENDING_BILLING_INFO", "DISAPPROVED"]
INSIGHT_FIELDS = ("adset_id,adset_name,campaign_id,campaign_name,spend,impressions,"
                  "inline_link_clicks,actions,action_values,account_currency")
ACCOUNT_FIELDS = "id,name,currency,timezone_name,account_status,disable_reason,spend_cap,amount_spent"
ACTIVITY_FIELDS = "event_time,event_type,object_id,object_name,object_type,extra_data,actor_name,application_name"
# Meta drosselt je Werbekonto; in der Zugriffsstufe „Limited access“ sperrt es nach wenigen Dutzend Aufrufen
# für einige Minuten (Fehlercodes 4, 17, 613, 80004). Dann einmal warten und wiederholen.
DROSSELUNG = re.compile(r'"code":\s*(4|17|613|80004)\b')
WARTEN = 310


def get(url, params=None):
    try:
        return http_json("GET", url, params)
    except ApiError as e:
        if not DROSSELUNG.search(str(e)):
            raise
        print(f"  Meta drosselt das Werbekonto; {WARTEN} Sekunden warten, dann einmal wiederholen …", flush=True)
        time.sleep(WARTEN)
        return http_json("GET", url, params)


def graph(path, token, version, **params):
    url = f"https://graph.facebook.com/{version}/{path}"
    params["access_token"] = token
    out, page = [], get(url, params)
    if "data" not in page:
        return page
    while True:
        out.extend(page.get("data", []))
        nxt = page.get("paging", {}).get("next")
        if not nxt:
            return out
        page = get(nxt)


def fetch_account(key, run_day, days, token, version):
    acc = ACCOUNTS[key]
    act = f"act_{acc['id']}"
    since = run_day - timedelta(days=days)
    result = {"konto": key, "account_id": acc["id"], "abgerufen": now_iso(), "api_version": version,
              "zeitraum": [since.isoformat(), run_day.isoformat()], "luecken": []}
    result["account"] = graph(act, token, version, fields=ACCOUNT_FIELDS)
    result["adsets"] = graph(f"{act}/adsets", token, version, fields=ADSET_FIELDS, limit=200,
                             filtering=json.dumps([{"field": "effective_status", "operator": "IN",
                                                    "value": ADSET_STATES}]))
    result["insights"] = graph(f"{act}/insights", token, version, level="adset", time_increment=1,
                               fields=INSIGHT_FIELDS, use_unified_attribution_setting="true", limit=500,
                               time_range=json.dumps({"since": since.isoformat(), "until": run_day.isoformat()}))
    try:
        result["activities"], result["aktivitaeten_abruf"] = activities(act, since, run_day, token, version)
    except ApiError as e:
        result["activities"] = None
        result["luecken"].append(f"Aktivitätsverlauf nicht abrufbar: {e}")
    return result


def activities(act, since, run_day, token, version):
    """Änderungsverlauf, am Stück und tageweise abgerufen und ohne Doppelungen zusammengeführt.

    Meta liefert `activities` unvollständig und nicht reproduzierbar: Beide Wege verlieren jeweils andere
    Einträge, am Stück können ganze Zeiträume fehlen. Was trotzdem fehlt, leitet `build_dataset.py` aus dem
    Vergleich mit dem letzten eigenen Datenstand ab."""
    stamp = lambda d: int(datetime.combine(d, datetime.min.time(), TZ).timestamp())  # noqa: E731
    am_stueck = graph(f"{act}/activities", token, version, since=stamp(since), limit=500, fields=ACTIVITY_FIELDS)
    tageweise, day = [], since
    while day <= run_day:
        tageweise += graph(f"{act}/activities", token, version, since=stamp(day),
                           until=stamp(day + timedelta(days=1)), limit=500, fields=ACTIVITY_FIELDS)
        day += timedelta(days=1)
    out, seen = [], set()
    for a in am_stueck + tageweise:
        key = (a.get("event_time"), a.get("event_type"), a.get("object_id"))
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out, {"am_stueck": len(am_stueck), "tageweise": len(tageweise), "zusammen": len(out)}


def test_account(key, run_day, days):
    """TEST-Modus: baut eine API-gleiche Antwort aus <startup>/testdaten/testdaten.json, Daten relativ zum Lauftag."""
    acc, spec = ACCOUNTS[key], read_json(FIXTURE)["konten"][key]
    since = run_day - timedelta(days=days)
    adsets, insights, activities = [], [], []
    for a in spec["adsets"]:
        camp = {"id": a["campaign_id"], "name": a.get("campaign_name") or ""}
        if a.get("campaign_daily_budget"):
            camp["daily_budget"] = str(round(a["campaign_daily_budget"] * 100))
        entry = {"id": a["id"], "name": a["name"], "status": a["status"], "effective_status": a["status"],
                 "campaign": camp}
        if a.get("daily_budget"):
            entry["daily_budget"] = str(round(a["daily_budget"] * 100))
        adsets.append(entry)
        for i, (spend, buys, revenue, clicks) in enumerate(a["tage"]):
            day = (run_day - timedelta(days=len(a["tage"]) - i)).isoformat()
            if spend:
                insights.append({"adset_id": a["id"], "adset_name": a["name"], "campaign_id": a["campaign_id"],
                                 "date_start": day, "date_stop": day, "spend": str(spend),
                                 "inline_link_clicks": str(clicks),
                                 "actions": [{"action_type": "omni_purchase", "value": str(buys)}] if buys else [],
                                 "action_values": [{"action_type": "omni_purchase", "value": str(revenue)}] if revenue else []})
        if a.get("aenderung_vor_tagen"):
            when = datetime.combine(run_day - timedelta(days=a["aenderung_vor_tagen"]), datetime.min.time(), TZ)
            activities.append({"event_type": "update_ad_set_budget", "object_id": a["id"], "object_name": a["name"],
                               "event_time": when.replace(hour=3).isoformat(), "actor_name": "Testperson",
                               "application_name": "Power Editor"})
    return {"konto": key, "account_id": acc["id"], "abgerufen": now_iso(), "api_version": "TESTDATEN",
            "zeitraum": [since.isoformat(), run_day.isoformat()], "testdaten": True,
            "luecken": ["TESTLAUF: erfundene Testdaten, keine echten Meta-Werte"],
            "account": {"currency": spec["currency"], "timezone_name": spec["timezone_name"]},
            "adsets": adsets, "insights": insights, "activities": activities}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=datetime.now(TZ).date().isoformat(), help="Lauftag (Zeitzone des Startups)")
    ap.add_argument("--tage", type=int, default=14, help="Tage Historie vor dem Lauftag")
    ap.add_argument("--konten", nargs="+", default=list(ACCOUNTS))
    args = ap.parse_args()
    require_real_data()
    run_day = date.fromisoformat(args.tag)
    if not TEST_MODE:
        token, = require_env("META_ACCESS_TOKEN")
        version = META_API_VERSION
    failed = []
    for key in args.konten:
        try:
            data = (test_account(key, run_day, args.tage) if TEST_MODE
                    else fetch_account(key, run_day, args.tage, token, version))
        except ApiError as e:
            failed.append(key)
            print(f"{key}: ABRUF FEHLGESCHLAGEN – {e}")
            continue
        path = write_json(raw_dir(run_day) / f"meta_{key}.json", data)
        print(f"{key}: {len(data['adsets'])} Adsets, {len(data['insights'])} Insight-Zeilen -> {path}")
        for gap in data["luecken"]:
            print(f"  LÜCKE: {gap}")
    if failed:
        raise SystemExit(f"Meta-Abruf fehlgeschlagen für: {', '.join(failed)}. Als Lücke melden, nichts schätzen; "
                         f"später mit --konten {' '.join(failed)} erneut abrufen.")


if __name__ == "__main__":
    main()
