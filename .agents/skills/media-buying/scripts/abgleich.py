"""Abgleich: Was wurde laut Meta tatsächlich geändert, von wem, und passt es zum Plan?

Jede Budget- und Statusänderung eines Adsets aus dem Meta-Änderungsverlauf wird einem Plan zugeordnet
(der letzte Plan, der höchstens PLAN_WIRKUNG Stunden vor der Änderung erstellt wurde) und bewertet:
„wie entschieden“, „abweichend“ oder „ohne Plan“. Ergebnis:
- Akte des Adsets: ein Eintrag je Änderung (wiederholbar, keine Doppelungen),
- Plan des Tages: `umsetzung_meta` je Zeile bzw. `ausserhalb_plan` (Dokumentation für Menschen),
- Rückgabe für die Übersicht: Änderungen je Adset und offene Fragen (Abweichungen ohne genannten Grund).
Gründe liefert Meta nie; sie kommen über `plan.py begruenden`.
"""
from datetime import datetime, timedelta

import akte
from common import CURRENCY_SIGN, in_runden, read_json, write_json

PLAN_WIRKUNG = 36  # Stunden: so lange gilt eine Änderung als Umsetzung des vorherigen Plans
STATUS = {"aktiv": "ACTIVE", "active": "ACTIVE", "inaktiv": "PAUSED", "inactive": "PAUSED", "paused": "PAUSED"}


def wert(v):
    if v is None:
        return "?"
    if isinstance(v, (int, float)):
        return f"{v:g} {CURRENCY_SIGN}"
    s = STATUS.get(str(v).strip().lower())
    return "AUS" if s == "PAUSED" else "AN" if s == "ACTIVE" else str(v)


def ziel_text(status, budget):
    return "AUS" if str(status).upper() == "PAUSED" else wert(budget)


def plaene():
    out = []
    for path in in_runden("AUSFUEHRUNGSPLAN_*_BUDGET.json"):
        plan = read_json(path)
        if plan.get("created_at"):
            out.append((datetime.fromisoformat(plan["created_at"]), path, plan))
    return sorted(out, key=lambda x: x[0])


def bewerten(ev, plans):
    """(Bewertung, Plan-Tupel oder None, Planzeile oder None) für eine Änderung."""
    if ev["art"] == "neu":
        return "neu", None, None
    t = datetime.fromisoformat(ev["zeit"])
    fitting = [p for p in plans if p[0] <= t <= p[0] + timedelta(hours=PLAN_WIRKUNG)]
    if not fitting:
        return "ohne Plan", None, None
    plan = fitting[-1]
    row = next((r for r in plan[2].get("rows", []) if r["id"] == ev["id"]), None)
    if not row:
        return "ohne Plan", plan, None
    target = str(row["target_status"]).upper()  # Pläne vom 18./19.10. speichern „active“/„paused“
    if ev["art"] == "status":
        ok = STATUS.get(str(ev["nachher"]).strip().lower()) == target
    else:
        ok = target == "ACTIVE" and ev["nachher"] == row["target_budget"]
    return ("wie entschieden" if ok else "abweichend"), plan, row


def satz(ev, bewertung, plan, row):
    was = (f"Neu angelegt mit {wert(ev['nachher'])}" if ev["art"] == "neu"
           else f"{'Status' if ev['art'] == 'status' else 'Budget'} {wert(ev['vorher'])} → {wert(ev['nachher'])}")
    wer = f" durch {ev['wer']}" if ev.get("wer") else ""
    wie = f" ({ev['werkzeug']})" if ev.get("werkzeug") else ""
    if bewertung == "neu":
        bezug = ""
    elif not plan:
        bezug = " Ohne Plan des Skills."
    elif not row:
        bezug = f" Adset nicht im Plan {plan[2]['change_id']}."
    else:
        v = row.get("vorschlag") or {}
        skill = ziel_text(v.get("status", row["target_status"]), v.get("budget", row["target_budget"]))
        entschieden = ziel_text(row["target_status"], row["target_budget"])
        bezug = (f" Wie entschieden in {plan[2]['change_id']} (Vorschlag Skill {skill})." if bewertung == "wie entschieden"
                 else f" Abweichend von {plan[2]['change_id']}: entschieden {entschieden}, Vorschlag Skill {skill}.")
    offen = " Grund nicht genannt." if bewertung in ("abweichend", "ohne Plan") else ""
    return f"{was}{wer}{wie}.{bezug}{offen}"


def abgleichen(events, rows_by_id, seit):
    """events: Änderungen aus dem Meta-Verlauf (build_dataset.ereignisse). rows_by_id: Adsets des Datenstands.
    seit: ISO-Zeit; Abweichungen danach ohne nachgetragenen Grund gelten als offene Fragen.
    Gibt ({adset_id: [Änderung mit Bewertung]}, [offene Fragen]) zurück."""
    plans = plaene()
    dirty, per_adset, fragen = set(), {}, []
    for ev in sorted(events, key=lambda e: e["zeit"]):
        r = rows_by_id.get(ev["id"])
        if not r:
            continue
        bewertung, plan, row = bewerten(ev, plans)
        text = satz(ev, bewertung, plan, row)
        akte.schreiben(r["account_id"], r["id"], r["name"],
                       akte.eintrag(ev["zeit"], "Änderung laut Meta", "meta", ev["key"], text), "meta", ev["key"])
        item = {**ev, "bewertung": bewertung, "plan": plan[2]["change_id"] if plan else None}
        per_adset.setdefault(ev["id"], []).append(item)
        if plan:
            entry = {k: ev.get(k) for k in ("key", "zeit", "art", "vorher", "nachher", "wer", "werkzeug")}
            entry["bewertung"] = bewertung
            target = row.setdefault("umsetzung_meta", []) if row else plan[2].setdefault("ausserhalb_plan", [])
            if not row:
                entry.update(id=ev["id"], name=r["name"])
            if all(e.get("key") != ev["key"] for e in target):
                target.append(entry)
                dirty.add(plan[1])
        t, grund = datetime.fromisoformat(ev["zeit"]), akte.letzter_grund(r["account_id"], r["id"])
        if (bewertung in ("abweichend", "ohne Plan") and t >= datetime.fromisoformat(seit)
                and not (grund and datetime.fromisoformat(grund) >= t)):
            fragen.append({**item, "konto": r["konto"], "name": r["name"], "text": text})
    for _, path, plan in plans:
        # Pläne aus dem früheren System (ohne "bericht") sind Historie: nur lesen, nicht umschreiben
        if path in dirty and "bericht" in plan:
            write_json(path, plan)
    return per_adset, fragen
