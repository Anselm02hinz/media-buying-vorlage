"""Korrektur, Freigabe, Begründung, Ausführung und Prüfung eines Budget-Ausführungsplans.

    python plan.py korrigieren --plan AUSFUEHRUNGSPLAN_YYYYMMDD_BUDGET.json --id <adset_id|Code>
                               (--budget 66 | --status PAUSED|ACTIVE [--budget …]) [--grund "..."] [--von <Name>]
    python plan.py freigeben  --plan ... --von <Entscheider> --wortlaut "..."
    python plan.py begruenden --id <adset_id> --grund "..." [--plan ...] [--von <Name>]
    python plan.py pruefen    --plan ... [--weg manuell|api]   # liest Ist-Werte, schreibt VERIFIKATION_*.json + Akten
    python plan.py ausfuehren --plan ...                        # nur mit Freigabe UND META_WRITE_ENABLED=1

`korrigieren` trägt eine Korrektur des Entscheiders vor der Freigabe ein; der Vorschlag des Skills mit Begründung
bleibt erhalten. Danach `render_report.py` ohne --entscheidungen neu rendern.
`freigeben` hält ausschließlich eine ausdrückliche menschliche Freigabe fest und schreibt die Entscheidung je Adset
in die Akten. `begruenden` hält einen vom Entscheider genannten Grund fest (für eine Korrektur, eine abweichende
Umsetzung oder eine Änderung ohne Plan), im Plan und in der Akte.
`ausfuehren` ist die einzige schreibende Funktion. Sie prüft vorher Freigabe, Schreibschalter und frischen Ist-Zustand,
ändert nur abweichende Zeilen des Plans (Tagesbudget/Status) und liest danach zurück.
"""
import argparse
import os

import akte
from common import (CURRENCY_SIGN, STARTUP, TEST_MODE, ApiError, datei, http_json, in_runden, now_iso, read_json,
                    require_env, require_real_data, write_json)
from render_report import LABEL, MIN_BUDGET, MIN_RULE, decision


def plan_path(value):
    return datei(value)


def changed(row):
    return row["budget"] != row["target_budget"] or row["status"] != row["target_status"]


def current_state(adset_id, token, version):
    data = http_json("GET", f"https://graph.facebook.com/{version}/{adset_id}",
                     {"fields": "status,effective_status,daily_budget", "access_token": token})
    budget = float(data["daily_budget"]) / 100 if data.get("daily_budget") else None
    return {"status": data.get("status"), "effective_status": data.get("effective_status"), "budget": budget}


def ziel(status, budget):
    return "AUS" if status == "PAUSED" else f"{budget:g} {CURRENCY_SIGN}"


def find_row(plan, key):
    row = next((r for r in plan["rows"] if key in (r["id"], r.get("code"))), None)
    if not row:
        raise SystemExit(f"{key}: nicht im Plan {plan['change_id']}.")
    return row


def cmd_korrigieren(plan, args):
    if plan["approval"]["status"] != "OFFEN":
        raise SystemExit("Plan ist bereits freigegeben; Korrekturen nur vorher. Abweichende Umsetzung mit "
                         "`begruenden` festhalten.")
    row = find_row(plan, args.id)
    status = args.status or row["target_status"]
    budget = args.budget if args.budget is not None else row["target_budget"]
    if status == "ACTIVE" and (budget is None or budget < MIN_BUDGET):
        raise SystemExit(f"Aktives Zielbudget {budget} unter {MIN_BUDGET} ({MIN_RULE}): pausieren statt kürzen.")
    row["target_status"], row["target_budget"] = status, budget
    row["decision"] = decision(row, status, budget)
    row["entscheidung"] = {"art": "korrigiert", "von": args.von or STARTUP["entscheider"], "at": now_iso(),
                           "grund": (args.grund or "").strip() or None}
    v = row.get("vorschlag") or {}
    print(f"{row.get('code', '')} {row['id']}: Vorschlag Skill {ziel(v.get('status'), v.get('budget'))} → "
          f"korrigiert {ziel(status, budget)}" + ("" if args.grund else " (Grund nicht genannt)")
          + ". Danach neu rendern: render_report.py --datenstand <D-…> ohne --entscheidungen.")


def cmd_freigeben(plan, args):
    if plan["approval"]["status"] != "OFFEN":
        raise SystemExit(f"Freigabe bereits {plan['approval']['status']}.")
    if not args.wortlaut.strip() or not args.von.strip():
        raise SystemExit("Freigabe braucht Wortlaut und Person.")
    plan["approval"] = {"status": "FREIGEGEBEN", "by": args.von, "at": now_iso(), "wortlaut": args.wortlaut}
    plan["status"] = "BEAUFTRAGT"
    for row in plan["rows"]:
        row.setdefault("entscheidung", {"art": "übernommen", "von": args.von, "at": plan["approval"]["at"]})
    akte_entscheidung(plan)
    fixes = sum(r["entscheidung"]["art"] == "korrigiert" for r in plan["rows"])
    print(f"{plan['change_id']}: FREIGEGEBEN durch {args.von}; {sum(map(changed, plan['rows']))} Änderungen, "
          f"{fixes} Korrekturen gegenüber dem Vorschlag.")


def akte_entscheidung(plan):
    for row in plan["rows"]:
        e, v = row["entscheidung"], row.get("vorschlag") or {}
        entschieden = f"{ziel(row['target_status'], row['target_budget'])} ({LABEL[row['decision']]})"
        if e["art"] == "korrigiert":
            text = (f"**Entscheidung {e['von']}: korrigiert** – Vorschlag Skill {ziel(v.get('status'), v.get('budget'))}"
                    f" → entschieden {entschieden}. Grund: {e.get('grund') or 'nicht genannt'}.")
        else:
            text = f"**Entscheidung {e['von']}: Vorschlag übernommen** – {entschieden}."
        text += f"\n\nFreigabe „{plan['approval']['wortlaut']}“ · Plan {plan['change_id']}"
        akte.schreiben(row["account_id"], row["id"], row["name"],
                       akte.eintrag(plan["approval"]["at"], f"Entscheidung · {plan['change_id']}", "entscheidung",
                                    plan["change_id"], text), "entscheidung", plan["change_id"])


def neuester_datenstand():
    found = in_runden("D-*-budget.json")
    return read_json(found[-1]) if found else {"rows": []}


def cmd_begruenden(args):
    """Grund des Entscheiders nachtragen: im Plan (falls angegeben) und in der Akte des Adsets."""
    grund, von, at = args.grund.strip(), args.von or STARTUP["entscheider"], now_iso()
    if not grund:
        raise SystemExit("Grund fehlt.")
    plan, path, row = None, None, None
    if args.plan:
        path = plan_path(args.plan)
        plan = read_json(path)
        row = next((r for r in plan["rows"] if args.id in (r["id"], r.get("code"))), None)
    info = row or next((r for r in neuester_datenstand()["rows"] if r["id"] == args.id), None)
    if not info:
        raise SystemExit(f"{args.id}: weder im Plan noch im neuesten Datenstand; Konto unbekannt.")
    if row:
        row.setdefault("gruende", []).append({"von": von, "at": at, "grund": grund})
        e = row.get("entscheidung") or {}
        if e.get("art") == "korrigiert" and not e.get("grund"):
            e["grund"] = grund
        write_json(path, plan)
    elif plan:
        plan.setdefault("gruende_ausserhalb_plan", []).append({"id": args.id, "von": von, "at": at, "grund": grund})
        write_json(path, plan)
    bezug = f" · Plan {plan['change_id']}" if plan else ""
    akte.schreiben(info["account_id"], info["id"], info.get("name"),
                   akte.eintrag(at, f"Grund von {von}", "grund", f"{info['id']}@{at}",
                                f"**Grund von {von}:** {grund}{bezug}"), "grund", f"{info['id']}@{at}")
    print(f"{info['id']}: Grund von {von} festgehalten" + (" (Plan und Akte)." if plan else " (Akte)."))


def refuse_test(plan, step):
    if plan.get("test") or TEST_MODE:
        raise SystemExit(f"TESTLAUF: {step} ist im Test gesperrt. Mit Testdaten wird nichts in Meta geändert "
                         "oder geprüft; der Test endet mit der Freigabe.")


def cmd_ausfuehren(plan, token, version):
    refuse_test(plan, "Ausführung")
    if plan["approval"]["status"] != "FREIGEGEBEN":
        raise SystemExit("Keine Freigabe im Plan. Ausführung verweigert.")
    if os.environ.get("META_WRITE_ENABLED") != "1":
        raise SystemExit("META_WRITE_ENABLED ist nicht 1: Schreibzugriff ist deaktiviert (AGENTS.md). "
                         "Plan dem Entscheider zur manuellen Umsetzung geben, danach `pruefen --weg manuell`.")
    log = []
    for row in filter(changed, plan["rows"]):
        entry = {"id": row["id"], "zeit": now_iso()}
        try:
            ist = current_state(row["id"], token, version)
            if (ist["status"], ist["budget"]) != (row["status"], row["budget"]):
                entry["ergebnis"] = f"ABWEICHUNG_VORHER {ist}; nicht geändert"
            else:
                params = {"access_token": token}
                if row["target_status"] == "ACTIVE" and row["target_budget"] != row["budget"]:
                    params["daily_budget"] = str(round(row["target_budget"] * 100))
                if row["target_status"] != row["status"]:
                    params["status"] = row["target_status"]
                http_json("POST", f"https://graph.facebook.com/{version}/{row['id']}", params)
                entry["ergebnis"] = "GESENDET"
        except ApiError as e:
            entry["ergebnis"] = f"FEHLER {e}"
        log.append(entry)
        print(f"{row['code']} {row['id']}: {entry['ergebnis']}")
    plan["execution"] = {"weg": "api", "status": "GESENDET_UNGEPRUEFT", "protokoll": log}


def cmd_pruefen(plan, path, token, version, weg, abschliessen):
    rows, ok = [], 0
    for row in plan["rows"]:
        try:
            ist = current_state(row["id"], token, version)
        except ApiError as e:
            ist = {"fehler": str(e)}
        target_budget = row["target_budget"] if row["target_status"] == "ACTIVE" else row["budget"]
        match = ist.get("status") == row["target_status"] and ist.get("budget") == target_budget
        ok += match
        rows.append({"id": row["id"], "code": row["code"], "soll": {"status": row["target_status"],
                     "budget": target_budget}, "ist": ist, "stimmt": match})
    status = "AUSGEFUEHRT_VERIFIZIERT" if ok == len(rows) else "TEILWEISE_AUSGEFUEHRT" if ok else "NICHT_AUSGEFUEHRT"
    ver_path = path.with_name(path.name.replace("AUSFUEHRUNGSPLAN", "VERIFIKATION"))
    write_json(ver_path, {"geprueft": now_iso(), "plan": path.name, "status": status, "rows": rows})
    plan["status"] = status
    plan["execution"] = {**plan.get("execution", {}), "weg": weg, "status": status, "geprueft": now_iso()}
    plan["verification_file"] = ver_path.name
    plan["execution_completed_at"] = now_iso() if status == "AUSGEFUEHRT_VERIFIZIERT" else None
    if not plan.get("akten_geschrieben") and (status == "AUSGEFUEHRT_VERIFIZIERT" or abschliessen):
        write_akten(plan, {r["id"]: r for r in rows})
        plan["akten_geschrieben"] = now_iso()
    print(f"{status}: {ok}/{len(rows)} Zeilen stimmen -> {ver_path.name}")
    if not plan.get("akten_geschrieben"):
        print("  Akten noch nicht ergänzt: nach Klärung erneut prüfen oder mit --abschliessen festschreiben.")
    for r in rows:
        if not r["stimmt"]:
            print(f"  ABWEICHUNG {r['code']} {r['id']}: Soll {r['soll']} Ist {r['ist']}")


def write_akten(plan, checks):
    """Prüfergebnis je Adset in die Akte (einmal je Plan)."""
    at = plan.get("execution", {}).get("geprueft") or now_iso()
    for row in plan["rows"]:
        check = checks[row["id"]]
        stand = "stimmt" if check["stimmt"] else f"ABWEICHUNG, Ist {check['ist']}"
        text = (f"**Geprüft ({plan['execution'].get('weg')}): {row['budget']:g} {CURRENCY_SIGN} → "
                f"{ziel(row['target_status'], row['target_budget'])} · {LABEL[row['decision']]} · {stand}**"
                f"\n\nPlan {plan['change_id']} · Bericht {plan['report_id']} · Freigabe {plan['approval']['by']}")
        akte.schreiben(row["account_id"], row["id"], row["name"],
                       akte.eintrag(at, f"Prüfung · {plan['change_id']}", "pruefung", plan["change_id"], text),
                       "pruefung", plan["change_id"])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("korrigieren", "freigeben", "begruenden", "pruefen", "ausfuehren"):
        p = sub.add_parser(name)
        p.add_argument("--plan", required=name != "begruenden")
        if name in ("korrigieren", "begruenden"):
            p.add_argument("--id", required=True, help="Adset-ID oder Code aus dem Bericht (z. B. J28)")
            p.add_argument("--grund", required=name == "begruenden")
            p.add_argument("--von", help="Standard: Entscheider aus startup.json")
        if name == "korrigieren":
            p.add_argument("--budget", type=float)
            p.add_argument("--status", choices=["ACTIVE", "PAUSED"])
        if name == "freigeben":
            p.add_argument("--von", required=True)
            p.add_argument("--wortlaut", required=True)
        if name == "pruefen":
            p.add_argument("--weg", choices=["manuell", "api"], default="manuell")
            p.add_argument("--abschliessen", action="store_true",
                           help="Akten auch bei Abweichungen mit dem geprüften Stand ergänzen")
    args = ap.parse_args()
    if args.cmd == "begruenden":
        cmd_begruenden(args)
        return
    path = plan_path(args.plan)
    plan = read_json(path)
    if args.cmd == "korrigieren":
        if args.budget is None and args.status is None:
            raise SystemExit("--budget oder --status angeben.")
        cmd_korrigieren(plan, args)
    elif args.cmd == "freigeben":
        cmd_freigeben(plan, args)
    else:
        refuse_test(plan, "Ausführung" if args.cmd == "ausfuehren" else "Prüfung")
        require_real_data()
        token, = require_env("META_ACCESS_TOKEN")
        version = os.environ.get("META_API_VERSION") or "v24.0"
        if args.cmd == "ausfuehren":
            cmd_ausfuehren(plan, token, version)
        else:
            if plan["approval"]["status"] != "FREIGEGEBEN":
                raise SystemExit("Plan ist nicht freigegeben; es gibt nichts zu prüfen.")
            cmd_pruefen(plan, path, token, version, args.weg, args.abschliessen)
    write_json(path, plan)


if __name__ == "__main__":
    main()
