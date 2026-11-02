"""Führt Meta- und Triple-Whale-Rohdaten eines Lauftags zu einem Datenstand je Adset zusammen.

Kennzahlen immer aus Summen: ROAS = Umsatz/Spend, CPA = Spend/Käufe, Link-CPC = Spend/Link-Klicks.
Nenner 0 oder fehlend -> None ("nicht berechenbar"). Keine Bewertung, keine Schwellen.

    python build_dataset.py [--tag YYYY-MM-DD]
Ergebnis: <startup>/runden/YYYY-MM-DD/D-YYYYMMDD-NNN-budget.json (vollständig, mit Tageswerten)
          und D-YYYYMMDD-NNN-uebersicht.md (Arbeitsgrundlage der KI: je aktivem Adset Kennzahlen, Tagesreihe,
          Änderungen mit Person, neueste Akteneinträge, Hinweise).
Nebenbei gleicht es die Meta-Änderungen mit den Plänen ab und schreibt sie in Akten und Pläne (abgleich.py).
"""
import argparse
import json
import re
from datetime import date, datetime, time, timedelta

import akte
from abgleich import STATUS, abgleichen
from common import (ACCOUNTS, CURRENCY_SIGN, ROOT, STARTUP, STARTUP_DIR, TW, TZ, in_runden, now_iso, raw_dir, read_json, runde,
                    separat_name, windows, write_json, write_text)

PURCHASE_TYPES = ("omni_purchase", "purchase", "offsite_conversion.fb_pixel_purchase")
CHANGE_EVENTS = ("update_ad_set_budget", "update_ad_set_run_status", "update_ad_set_bid_strategy",
                 "update_ad_set_bid_amount", "update_campaign_budget", "update_campaign_run_status")
ADSET_EVENTS = {"update_ad_set_budget": "budget", "update_ad_set_run_status": "status", "create_ad_set": "neu"}
TAGE_IN_UEBERSICHT = 7      # Tagesreihe je Adset: so viele abgeschlossene Tage plus heute
AENDERUNGEN_IN_UEBERSICHT = 8


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def action_value(entries, types=PURCHASE_TYPES):
    by_type = {e.get("action_type"): num(e.get("value")) for e in entries or []}
    for t in types:
        if t in by_type:
            return by_type[t]
    return 0.0


def aggregate(daily, since, until):
    rows = [v for d, v in daily.items() if since.isoformat() <= d <= until.isoformat()]
    s = {k: sum(r.get(k) or 0.0 for r in rows) for k in ("spend", "purchases", "revenue", "link_clicks")}
    return {
        "von": since.isoformat(), "bis": until.isoformat(), "tage_mit_daten": len(rows),
        "spend": round(s["spend"], 2), "kaeufe": s["purchases"], "umsatz": round(s["revenue"], 2),
        "link_klicks": s["link_clicks"],
        "roas": round(s["revenue"] / s["spend"], 2) if s["spend"] else None,
        "cpa": round(s["spend"] / s["purchases"], 2) if s["purchases"] else None,
        "link_cpc": round(s["spend"] / s["link_clicks"], 2) if s["link_clicks"] else None,
    }


def sum_days(series):
    """Addiert mehrere Tagesreihen {datum: {kennzahl: wert}} zu einer."""
    out = {}
    for daily in series:
        for day, values in daily.items():
            target = out.setdefault(day, {})
            for k, v in values.items():
                target[k] = target.get(k, 0.0) + (v or 0.0)
    return out


def meta_daily(insights):
    out = {}
    for r in insights:
        day = out.setdefault(r["adset_id"], {}).setdefault(r["date_start"], {})
        day["spend"] = num(r.get("spend"))
        day["purchases"] = action_value(r.get("actions"))
        day["revenue"] = action_value(r.get("action_values"))
        day["link_clicks"] = num(r.get("inline_link_clicks"))
    return out


def tw_daily(raw):
    resp = raw.get("antwort")
    rows = resp if isinstance(resp, list) else (resp or {}).get("data") or (resp or {}).get("rows") or []
    out = {}
    for r in rows:
        adset, day = str(r.get("adset_id") or ""), str(r.get("event_date") or "")[:10]
        if adset and day:
            out.setdefault(adset, {})[day] = {"purchases": num(r.get("purchases")),
                                               "revenue": num(r.get("revenue")), "spend": num(r.get("spend"))}
    return out


def parse_time(value):
    value = re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", str(value).replace("Z", "+00:00"))
    return datetime.fromisoformat(value).astimezone(TZ)


def change_values(event_type, extra):
    """Vorher/Nachher aus `extra_data` einer Meta-Aktivität (JSON-Text, Budgets in Cent).

    Erwartet `old_value`/`new_value`, flach oder verschachtelt ({"old_value": {"old_value": 8800, ...}}).
    Das genaue Format ist beim ersten echten Abruf zu bestätigen; Unlesbares ergibt (None, None).
    """
    try:
        data = json.loads(extra) if isinstance(extra, str) else (extra or {})
    except ValueError:
        return None, None
    if not isinstance(data, dict):
        return None, None

    def pick(value, key):
        while isinstance(value, dict):
            value = value.get(key, value.get("value"))
        return value

    old, new = pick(data.get("old_value"), "old_value"), pick(data.get("new_value"), "new_value")
    if "budget" in event_type:
        old, new = (num(v) / 100 if re.fullmatch(r"\d+(\.\d+)?", str(v)) else None for v in (old, new))
    return old, new


def last_changes(meta_raw):
    """Letzte Budget-/Statusänderung je Adset mit Vorher/Nachher, soweit bekannt.

    Quellen: Meta-Aktivitäten, ergänzt um verifizierte frühere Ausführungspläne.
    """
    found = {}

    def note(adset_id, when, source, art, old=None, new=None, wer=None):
        t = parse_time(when)
        prev = found.get(adset_id)
        if not prev or t > prev["zeit"] or (t == prev["zeit"] and prev["vorher"] is None and old is not None):
            found[adset_id] = {"zeit": t, "quelle": source, "art": art, "vorher": old, "nachher": new, "wer": wer}

    for raw in meta_raw.values():
        for a in raw.get("activities") or []:
            event = a.get("event_type")
            if event in CHANGE_EVENTS and a.get("object_id") and a.get("event_time"):
                old, new = change_values(event, a.get("extra_data"))
                source = a["application_name"] if a.get("abgeleitet") else f"Meta-Aktivität {event}"
                note(a["object_id"], a["event_time"], source,
                     "budget" if "budget" in event else "status", old, new, a.get("actor_name"))
    for path in in_runden("AUSFUEHRUNGSPLAN_*_BUDGET.json"):
        plan = read_json(path)
        when = plan.get("execution_completed_at")
        if not when or "VERIFIZIERT" not in str(plan.get("status", "")):
            continue
        source = path.name
        for row in plan.get("rows", []):
            old_status, new_status = str(row.get("status", "")).upper(), str(row.get("target_status", "")).upper()
            if old_status != new_status:
                note(row["id"], when, source, "status", old_status, new_status)
            elif row.get("budget") != row.get("target_budget"):
                note(row["id"], when, source, "budget", row.get("budget"), row.get("target_budget"))
    return {k: {**v, "zeit": v["zeit"].isoformat(timespec="minutes")} for k, v in found.items()}


def aus_datenstand(meta_raw, prev):
    """Ergänzt Budget- und Statuswechsel seit dem letzten eigenen Datenstand, die im Meta-Verlauf fehlen.

    Meta liefert den Verlauf unvollständig (siehe fetch_meta.activities). Weicht der Wert eines Adsets vom
    letzten Datenstand ab und erklärt kein Verlaufseintrag danach den heutigen Wert, wird ein abgeleiteter
    Eintrag angehängt (`abgeleitet: True`, ohne Person). Zeitpunkt: letzte Bearbeitung laut Meta
    (`updated_time`), mindestens der letzte bekannte Eintrag; also geschätzt. Gibt die Anzahl zurück."""
    if not prev:
        return 0
    since, before, n = parse_time(prev["erstellt"]), {r["id"]: r for r in prev["rows"]}, 0
    for raw in meta_raw.values():
        acts = raw["activities"] = raw.get("activities") or []
        logged = {}
        for a in acts:
            if a.get("object_id") and a.get("event_time") and parse_time(a["event_time"]) > since:
                logged.setdefault((a["object_id"], a.get("event_type")), []).append(a)
        for s in raw["adsets"]:
            p = before.get(s["id"])
            if not p:
                continue
            checks = []
            if p.get("budget_ebene") == "adset" and p.get("budget") is not None and s.get("daily_budget"):
                checks.append(("update_ad_set_budget", p["budget"], num(s["daily_budget"]) / 100))
            if p.get("status") and s.get("status"):
                checks.append(("update_ad_set_run_status", str(p["status"]).upper(), str(s["status"]).upper()))
            for event, old, new in checks:
                if old == new:
                    continue
                t = max([since] + ([parse_time(s["updated_time"])] if s.get("updated_time") else []))
                evs = sorted(logged.get((s["id"], event), []), key=lambda a: parse_time(a["event_time"]))
                if evs:
                    _, last = change_values(event, evs[-1].get("extra_data"))
                    if "status" in event:
                        last = STATUS.get(str(last).strip().lower())
                    if last == new:
                        continue
                    old, t = (last if last is not None else old), max(t, parse_time(evs[-1]["event_time"]))
                if "budget" in event:
                    extra = {"old_value": round(old * 100), "new_value": round(new * 100)}
                else:
                    label = {"ACTIVE": "Aktiv", "PAUSED": "Inaktiv"}
                    extra = {"old_value": label.get(old, old), "new_value": label.get(new, new)}
                acts.append({"event_time": t.isoformat(timespec="seconds"), "event_type": event, "object_id": s["id"],
                             "object_name": s.get("name"), "extra_data": json.dumps(extra), "abgeleitet": True,
                             "application_name": f"nicht im Meta-Verlauf, abgeleitet aus {prev['id']}"})
                n += 1
    return n


def phase_text(row):
    """Phase seit der letzten Änderung als Satz, aus dem Datenstand erzeugt (nicht von der KI)."""
    def value(v):
        if isinstance(v, (int, float)):
            return f"{v:g} {CURRENCY_SIGN}"
        s = str(v).upper()
        return "AUS" if s in ("PAUSED", "INACTIVE") else "AN" if s == "ACTIVE" else str(v)

    change, parts = row.get("letzte_aenderung"), []
    if change:
        t = change["zeit"]
        what = (f"{value(change['vorher'])} → {value(change['nachher'])}" if change.get("vorher") is not None
                else f"Änderung ohne bekannte Werte ({change['quelle']})")
        who = f" ({change['wer']})" if change.get("wer") else ""
        parts.append(f"Seit {t[8:10]}.{t[5:7]}. {t[11:16]} Uhr: {what}{who}")
    else:
        parts.append("Keine Budget- oder Statusänderung im Abrufzeitraum bekannt")
    first = row.get("erster_liefertag")
    if first and not row.get("liefert_schon_vor_zeitraum"):
        parts.append(f"Erster Liefertag {first[8:10]}.{first[5:7]}.")
    return ". ".join(p.rstrip(".") for p in parts) + "."


def ereignisse(meta_raw):
    """Budget-, Status- und Neuanlage-Ereignisse je Adset aus dem Meta-Verlauf, mit Person und Werkzeug.
    Die Veröffentlichung neuer Adsets („Ausstehend“ → Aktiv) zählt nicht als Statusänderung."""
    out = []
    for raw in meta_raw.values():
        for a in raw.get("activities") or []:
            art = ADSET_EVENTS.get(a.get("event_type"))
            if not art or not a.get("object_id") or not a.get("event_time"):
                continue
            old, new = change_values(a["event_type"], a.get("extra_data"))
            if art == "neu":
                new = num(new) / 100 if re.fullmatch(r"\d+(\.\d+)?", str(new)) else None
            if art == "status" and "ausstehend" in str(old).lower():
                continue
            out.append({"key": f"{a['object_id']}|{a['event_time']}|{a['event_type']}", "id": a["object_id"],
                        "zeit": parse_time(a["event_time"]).isoformat(timespec="minutes"), "art": art,
                        "vorher": old, "nachher": new, "wer": a.get("actor_name"),
                        "werkzeug": a.get("application_name")})
    return out


def hinweise(row, run_day, win, events):
    """Nüchterne Hinweise je Adset aus den Daten. Keine Bewertung, keine Schwellen."""
    out, md = [], row.get("meta_taeglich") or {}
    first = row.get("erster_liefertag")
    if row["effective_status"] == "ACTIVE" and not any(v.get("spend") for v in md.values()):
        start = parse_time(row["start_time"]).date() if row.get("start_time") else None
        out.append("noch keine Auslieferung seit Start" if start and start >= win["y"][0]
                   else "liefert nicht: kein Spend im Abrufzeitraum")
    elif first == run_day.isoformat():
        out.append("erster Liefertag heute (unvollständig)")
    elif first == win["y"][0].isoformat() and not row.get("liefert_schon_vor_zeitraum"):
        out.append("gestern erster vollständiger Liefertag")
    for ev in events:
        if str(ev.get("werkzeug") or "").startswith("nicht im Meta-Verlauf"):
            out.append(f"Änderung {ev['zeit'][8:10]}.{ev['zeit'][5:7]}. {ev['werkzeug']}; Zeitpunkt geschätzt "
                       "(letzte Bearbeitung laut Meta), Person unbekannt")
        if ev["art"] == "status" and str(ev["nachher"]).lower() in ("aktiv", "active") and \
                str(ev["vorher"]).lower() in ("inaktiv", "inactive", "paused"):
            out.append(f"reaktiviert am {ev['zeit'][8:10]}.{ev['zeit'][5:7]}.")
    budgets = [ev for ev in events if ev["art"] in ("budget", "neu") and ev["nachher"] is not None]
    if row["budget_ebene"] == "adset" and budgets and budgets[-1]["nachher"] != row["budget"]:
        upd = row.get("updated_time")
        when = f"; Meta meldet letzte Bearbeitung {parse_time(upd):%d.%m. %H:%M}" if upd else ""
        out.append(f"Budget {row['budget']:g} {CURRENCY_SIGN} passt nicht zum letzten Verlaufswert "
                   f"{budgets[-1]['nachher']:g} {CURRENCY_SIGN}{when}. Änderungsverlauf lückenhaft, Phase unsicher")
    if (row["meta"].get("d7") or {}).get("spend") and not row.get("tw") and TW["aktiv"]:
        out.append("TW: keine Zuordnung")
    return out


def _cell(m):
    if not m:
        return "–"
    roas = f"{m['roas']:.2f}" if m.get("roas") is not None else "–"
    return f"{roas} · {m['kaeufe']:g} K · {m['spend']:.0f}"


def _cpc(m):
    return f"{m['link_cpc']:.2f}" if m and m.get("link_cpc") is not None else "–"


def _tage(row, data):
    """Tagesreihe: Spend/Käufe/ROAS (TW-Käufe) der letzten Tage, heute markiert."""
    md, td = row.get("meta_taeglich") or {}, row.get("tw_taeglich") or {}
    end = date.fromisoformat(data["lauftag"])
    parts = []
    for i in range(TAGE_IN_UEBERSICHT, -1, -1):
        d = (end - timedelta(days=i)).isoformat()
        m, t = md.get(d) or {}, td.get(d) or {}
        if not m.get("spend") and not t.get("purchases"):
            if parts:
                parts.append(f"{d[8:10]}. 0")
            continue
        roas = f"{m['revenue'] / m['spend']:.2f}" if m.get("spend") else "–"
        tw = f" ({t.get('purchases', 0):g})" if td else ""
        parts.append(f"{d[8:10]}. {m.get('spend', 0):.0f}/{m.get('purchases', 0):g}/{roas}{tw}"
                     + (" heute" if i == 0 else ""))
    return " · ".join(parts) or "keine Auslieferung"


def _aenderung(ev):
    t = f"{ev['zeit'][8:10]}.{ev['zeit'][5:7]}."
    wer = f" {ev['wer'].split()[0]}" if ev.get("wer") else ""
    def fmt(v):
        if v is None:
            return "?"
        if isinstance(v, (int, float)):
            return f"{v:g}"
        return "aus" if str(v).lower() in ("inaktiv", "inactive", "paused") else "an"

    was = f"neu {fmt(ev['nachher'])}" if ev["art"] == "neu" else f"{fmt(ev['vorher'])}→{fmt(ev['nachher'])}"
    mark = {"abweichend": " ABWEICHEND", "ohne Plan": ""}.get(ev.get("bewertung"), "")
    return f"{t} {was}{wer}{mark}"


def overview(data):
    """Arbeitsgrundlage der KI. A: zu entscheiden (alles je Adset), B: seit gestern pausiert/geändert,
    C: Kampagnenbudgets und Separates, D: ruhend (nur gezählt). Vollständiges im Datenstand und in den Akten."""
    rows = data["rows"]
    in_a = lambda r: r["effective_status"] == "ACTIVE" and r["budget_ebene"] == "adset" and not r.get("separat")  # noqa: E731
    in_c = lambda r: r["effective_status"] == "ACTIVE" and not in_a(r)  # noqa: E731
    in_b = lambda r: r["effective_status"] != "ACTIVE" and r.get("bewegung")  # noqa: E731
    a, b, c = [r for r in rows if in_a(r)], [r for r in rows if in_b(r)], [r for r in rows if in_c(r)]
    d = len(rows) - len(a) - len(b) - len(c)
    k = data.get("kontrolle", {})
    lines = [f"# Übersicht {data['id']}" + (" · TESTLAUF" if data["test"] else ""), "",
             f"Lauftag {data['lauftag']} · Fenster: gestern {data['fenster']['y'][0]}, 3 T ab {data['fenster']['d3'][0]}, "
             f"7 T ab {data['fenster']['d7'][0]} · heute unvollständig, nicht in den Fenstern.",
             f"Lesehilfe: Fenster „ROAS · Käufe · Spend ({CURRENCY_SIGN})“. Tage „Spend/Käufe/ROAS (TW-Käufe)“. "
             "Meta und TW getrennt, nie addieren. Änderungen „Datum alt→neu Person“. Akte = neueste Begründungen "
             "(Vorschlag des Skills, Entscheidung des Entscheiders, Gründe); vollständig in "
             f"`{STARTUP_DIR.name}/akten/meta_<konto>_<adset>.md`, alle Zahlen in `{data['id']}-budget.json`.", "",
             f"**Kontrolle:** {k.get('aktiv_meta', '?')} aktive Adsets laut Meta = {len(a)} zu entscheiden (A) "
             f"+ {len(c)} mit Kampagnenbudget oder separat (C)."
             + ("" if k.get("aktiv_meta") == len(a) + len(c) else " **ABWEICHUNG – Datenstand prüfen.**"), ""]
    if data["luecken"]:
        lines += ["**Lücken:** " + " · ".join(data["luecken"]), ""]
    fragen = data.get("offene_fragen") or []
    if fragen:
        by_adset = {}
        for f in fragen:
            by_adset.setdefault((f["konto"], f["name"] or "", f["id"]), []).append(f)
        lines += [f"## Offene Fragen an {STARTUP['entscheider']} · {len(fragen)} Änderungen an {len(by_adset)} Adsets "
                  "seit gestern ohne Plan oder abweichend, Grund nicht genannt", "",
                  "Einzelheiten je Adset unter „Änderungen“ (A) bzw. in Abschnitt B und in der Akte.", ""]
        for (konto, name, adset_id), group in sorted(by_adset.items()):
            what = " · ".join(_aenderung(f) for f in group)
            lines.append(f"- {ACCOUNTS[konto]['label'].split(' · ')[0]} · {name[:60]} (`{adset_id}`): {what}")
        lines.append("")
    lines += [f"## A · Zu entscheiden · {len(a)}", ""]
    for key in ACCOUNTS:
        group = sorted((r for r in a if r["konto"] == key), key=lambda r: r["name"] or "")
        if not group:
            continue
        lines += [f"### {ACCOUNTS[key]['label']} · {len(group)}", ""]
        for r in group:
            m, t = r["meta"], r.get("tw") or {}
            lines.append(f"**{(r['name'] or '')[:80]}** · `{r['id']}` · {r['budget']:g} {CURRENCY_SIGN} · "
                         f"{r.get('campaign_name') or ''}")
            lines.append(f"- Phase: {r['phase']}")
            if (m.get("d7") or {}).get("spend") or (t.get("d7") or {}).get("kaeufe"):
                lines.append(f"- Fenster: gestern {_cell(m.get('y'))} / TW {_cell(t.get('y'))} | 3 T {_cell(m.get('d3'))}"
                             f" / TW {_cell(t.get('d3'))} | 7 T {_cell(m.get('d7'))} / TW {_cell(t.get('d7'))} | "
                             f"seit Änd. {_cell(m.get('seit_aenderung'))} / TW {_cell(t.get('seit_aenderung'))} | "
                             f"Link-CPC 3 T {_cpc(m.get('d3'))}, 7 T {_cpc(m.get('d7'))}")
            else:
                lines.append("- Fenster: keine Auslieferung in den letzten 7 abgeschlossenen Tagen")
            lines.append(f"- Tage: {_tage(r, data)}")
            evs = r.get("aenderungen") or []
            if evs:
                more = f"(+{len(evs) - AENDERUNGEN_IN_UEBERSICHT} ältere) " if len(evs) > AENDERUNGEN_IN_UEBERSICHT else ""
                lines.append("- Änderungen: " + more + " · ".join(
                    _aenderung(e) for e in evs[-AENDERUNGEN_IN_UEBERSICHT:]))
            for entry in r.get("akte") or []:
                lines.append(f"- Akte: {entry}")
            if r.get("hinweise"):
                lines.append("- Hinweise: " + "; ".join(r["hinweise"]))
            lines.append("")
    if b:
        lines += [f"## B · Seit gestern pausiert, geändert oder noch mit Spend, jetzt nicht aktiv · {len(b)}", ""]
        for r in sorted(b, key=lambda r: (r["konto"], r["name"] or "")):
            budget = f"{r['budget']:g} {CURRENCY_SIGN}" if r["budget"] is not None else "ohne Tagesbudget"
            lines.append(f"- {ACCOUNTS[r['konto']]['label'].split(' · ')[0]} · {(r['name'] or '')[:60]} (`{r['id']}`) · "
                         f"{budget} · {r['effective_status']} · {r['phase']} Gestern {_cell(r['meta'].get('y'))}.")
        lines.append("")
    if c:
        lines += [f"## C · Kampagnenbudget oder separat (nicht im Plan) · {len(c)}", ""]
        groups = {}
        for r in c:
            label = (f"separat laut startup.json: {r['separat']}" if r.get("separat")
                     else f"{r['campaign_name'] or r['campaign_id']} · Budget auf Ebene {r['budget_ebene'] or 'unbekannt'}")
            groups.setdefault((r["konto"], label, r["budget"]), []).append(r)
        for (key, label, budget), group in groups.items():
            d3 = [r["meta"].get("d3") or {} for r in group]
            spend, rev = sum(x.get("spend") or 0 for x in d3), sum(x.get("umsatz") or 0 for x in d3)
            roas = f"{rev / spend:.2f}" if spend else "–"
            lines.append(f"- {ACCOUNTS[key]['label'].split(' · ')[0]} · {label}"
                         + (f" · {budget:g} {CURRENCY_SIGN}" if budget is not None else "")
                         + f" · {len(group)} aktive Sets · 3 T Meta {roas} auf {spend:.0f} {CURRENCY_SIGN}")
        lines.append("")
    lines += [f"## D · Ruhend · {d}", "", "Pausiert, gestern und heute kein Spend, keine Änderung seit gestern. "
              "Nur im Datenstand.", ""]
    return "\n".join(lines)


def next_id(run_day):
    prefix = f"D-{run_day:%Y%m%d}-"
    used = [int(p.name[len(prefix):len(prefix) + 3]) for p in runde(run_day).glob(prefix + "*")]
    return f"{prefix}{max(used, default=0) + 1:03d}"


def budget_of(adset):
    camp = adset.get("campaign") or {}
    if adset.get("daily_budget"):
        return num(adset["daily_budget"]) / 100, "adset"
    if camp.get("daily_budget"):
        return num(camp["daily_budget"]) / 100, "kampagne"
    return None, "lifetime" if adset.get("lifetime_budget") or camp.get("lifetime_budget") else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=datetime.now(TZ).date().isoformat())
    args = ap.parse_args()
    run_day = date.fromisoformat(args.tag)
    folder = raw_dir(run_day)
    meta_raw = {k: read_json(folder / f"meta_{k}.json") for k in ACCOUNTS if (folder / f"meta_{k}.json").exists()}
    tw_path = folder / "triple_whale.json"
    tw_raw = read_json(tw_path) if tw_path.exists() else None
    tw = tw_daily(tw_raw) if tw_raw else {}
    win = windows(run_day)
    vorher = [p for p in in_runden("D-*-budget.json") if p.name[2:10] <= f"{run_day:%Y%m%d}"]
    prev = read_json(vorher[-1]) if vorher else None
    abgeleitet = aus_datenstand(meta_raw, prev)
    changes = last_changes(meta_raw)
    gaps = [f"Meta-Rohdaten fehlen: {k}" for k in ACCOUNTS if k not in meta_raw]
    if abgeleitet:
        gaps.append(f"{abgeleitet} Budget-/Statuswechsel fehlen im Meta-Verlauf; aus {prev['id']} abgeleitet "
                    "(Zeitpunkt geschätzt, Person unbekannt)")
    if not TW["aktiv"]:
        gaps.append("Triple Whale laut startup.json nicht genutzt; TW-Spalten bleiben leer.")
    elif not tw_raw:
        gaps.append("Triple-Whale-Rohdaten fehlen; TW-Spalten bleiben leer.")
    rows, accounts = [], {}
    for key, raw in meta_raw.items():
        gaps += [f"{key}: {g}" for g in raw.get("luecken", [])]
        tz = (raw.get("account") or {}).get("timezone_name")
        if tz and tz != STARTUP["zeitzone"]:
            gaps.append(f"{key}: Kontozeitzone {tz} statt {STARTUP['zeitzone']}")
        daily = meta_daily(raw["insights"])
        ids = set(daily) | {a["id"] for a in raw["adsets"]}
        accounts[key] = {
            "meta": {w: aggregate(sum_days(daily[i] for i in daily), *rng) for w, rng in win.items()},
            "tw": ({w: aggregate(sum_days(tw[i] for i in ids if i in tw), *rng) for w, rng in win.items()}
                   if tw_raw else None),
            "umfang": "alle Adsets des Kontos mit Auslieferung im Zeitraum, auch inzwischen pausierte",
        }
        for a in raw["adsets"]:
            md = daily.get(a["id"], {})
            if a.get("effective_status") != "ACTIVE" and not any(v["spend"] for v in md.values()):
                continue
            budget, level = budget_of(a)
            spend_days = sorted(d for d, v in md.items() if v["spend"] > 0)
            change = changes.get(a["id"])
            row = {
                "konto": key, "account_id": ACCOUNTS[key]["id"], "id": a["id"], "name": a.get("name"),
                "campaign_id": (a.get("campaign") or {}).get("id"), "campaign_name": (a.get("campaign") or {}).get("name"),
                "status": a.get("status"), "effective_status": a.get("effective_status"),
                "budget": budget, "budget_ebene": level, "bid_strategy": a.get("bid_strategy"),
                "start_time": a.get("start_time"), "updated_time": a.get("updated_time"),
                "erster_liefertag": spend_days[0] if spend_days else None,
                "liefert_schon_vor_zeitraum": bool(spend_days) and spend_days[0] == raw["zeitraum"][0],
                "letzte_aenderung": change,
                "meta": {w: aggregate(md, *rng) for w, rng in win.items()},
                "tw": None, "meta_taeglich": md, "tw_taeglich": tw.get(a["id"]),
            }
            if change:
                change_day = parse_time(change["zeit"]).date()
                if change_day <= win["y"][1]:
                    row["meta"]["seit_aenderung"] = aggregate(md, change_day, win["y"][1])
            if a["id"] in tw:
                row["tw"] = {w: aggregate(tw[a["id"]], *rng) for w, rng in row_windows(row, win).items()}
            row["phase"] = phase_text(row)
            row["separat"] = separat_name(a["id"], row["campaign_id"])
            rows.append(row)
    # Abgleich mit den Plänen, Akten fortschreiben; danach die neuesten Begründungen je Adset lesen
    seit = datetime.combine(win["y"][0], time.min, TZ).isoformat(timespec="minutes")
    events = ereignisse(meta_raw)
    per_adset, fragen = abgleichen(events, {r["id"]: r for r in rows}, seit)
    for row in rows:
        evs = per_adset.get(row["id"], [])
        row["aenderungen"] = evs
        row["hinweise"] = hinweise(row, run_day, win, evs)
        md = row["meta_taeglich"]
        row["bewegung"] = bool(any(e["zeit"] >= seit for e in evs) or (md.get(win["y"][0].isoformat()) or {}).get("spend")
                               or (md.get(run_day.isoformat()) or {}).get("spend"))
        if row["effective_status"] == "ACTIVE" and row["budget_ebene"] == "adset" and not row.get("separat"):
            row["akte"] = akte.auszug(row["account_id"], row["id"])
    unsicher = [r for r in rows if r["effective_status"] == "ACTIVE"
                and any("passt nicht zum letzten Verlaufswert" in h for h in r["hinweise"])]
    if unsicher:
        gaps.append(f"Änderungsverlauf lückenhaft: bei {len(unsicher)} aktiven Adsets passt das Budget nicht zum "
                    "letzten Verlaufswert (Hinweis je Adset in der Übersicht)")
    dataset_id = next_id(run_day)
    test = any(r.get("testdaten") for r in meta_raw.values())
    data = {
        "id": dataset_id, "test": test, "erstellt": now_iso(), "lauftag": run_day.isoformat(),
        "zeitzone": STARTUP["zeitzone"],
        "fenster": {w: [a.isoformat(), b.isoformat()] for w, (a, b) in win.items()},
        "hinweise": ["'heute' ist unvollständig.", "'seit_aenderung' beginnt mit dem Änderungstag (Mischtag)."],
        "meta": {"api_version": next(iter(meta_raw.values()), {}).get("api_version"),
                 "waehrung": {k: (r.get("account") or {}).get("currency") for k, r in meta_raw.items()},
                 "attribution": "Adset-Attributionseinstellung (use_unified_attribution_setting)",
                 "kauf_action_type": PURCHASE_TYPES[0], "link_klicks": "inline_link_clicks"},
        "tw": {k: tw_raw.get(k) for k in ("modell", "fenster", "shop", "abgerufen")} if tw_raw else None,
        "rohdaten": folder.relative_to(ROOT).as_posix(), "luecken": gaps, "konten": accounts,
        "kontrolle": {"aktiv_meta": sum(a.get("effective_status") == "ACTIVE"
                                        for raw in meta_raw.values() for a in raw["adsets"])},
        "offene_fragen": fragen, "rows": rows,
    }
    path = write_json(runde(run_day) / f"{dataset_id}-budget.json", data)
    summary = runde(run_day) / f"{dataset_id}-uebersicht.md"
    write_text(summary, overview(data))
    print(f"{dataset_id}: {len(rows)} Adsets, {len(gaps)} Lücken -> {path}")
    print(f"Übersicht (Arbeitsgrundlage: Kennzahlen, Tagesreihe, Änderungen, Akte je aktivem Adset) -> {summary}")
    print(f"Abgleich: {sum(map(len, per_adset.values()))} Änderungen laut Meta in den Akten, "
          f"{len(fragen)} offene Fragen an {STARTUP['entscheider']}")
    for g in gaps:
        print(f"  LÜCKE: {g}")


def row_windows(row, win):
    out = dict(win)
    if "seit_aenderung" in row["meta"]:
        m = row["meta"]["seit_aenderung"]
        out["seit_aenderung"] = (date.fromisoformat(m["von"]), date.fromisoformat(m["bis"]))
    return out


if __name__ == "__main__":
    main()
