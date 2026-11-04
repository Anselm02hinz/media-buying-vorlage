"""Erzeugt aus Datenstand und KI-Entscheidungen den HTML-Budgetbericht und den Ausführungsplan.

Erster Lauf: Entscheidungen als JSON (vorübergehend, z. B. in runden/YYYY-MM-DD/rohdaten/):
    {"auftrag": "Wortlaut des Auftrags des Entscheiders mit Zeit, z. B. „Mach mein Media Buying für heute“ (TT.MM. hh:mm)",
     "kopf": "Kernaussage in einem Satz.",
     "notizen": [{"titel": "Gezielt hoch", "text": "..."}, ...],
     "kontohinweise": {"<kontoschlüssel aus startup.json>": "Alle aktiven Sets halten."},
     "separat": "Text zu CBOs/Follower/Sonstigem (optional)",
     "grenzen": ["zusätzliche Hinweise zu Datenstand und Grenzen (optional)"],
     "entscheidungen": [{"id": "<adset_id>", "ziel_status": "ACTIVE|PAUSED", "ziel_budget": 44,
                         "grund": "...", "regeln": ["MB-0003 v1", "L-03"], "kurzname": "Produkt A · Test 1"}]}
    In "regeln" stehen Regel-IDs mit Version und die IDs bestätigter Learnings, die den Vorschlag geprägt haben.
    python render_report.py --datenstand D-…-budget.json --entscheidungen entscheidungen.json

Die Phase seit der letzten Änderung kommt aus dem Datenstand (build_dataset.py), nicht aus den Entscheidungen.
Adsets, die startup.json unter "separat" führt, gehören nicht in die Entscheidungen.

Korrekturen des Entscheiders: `plan.py korrigieren` (Zielwert und Grund; der Vorschlag des Skills mit Begründung
bleibt erhalten), Berichtstexte unter "bericht" direkt im Plan; danach ohne --entscheidungen neu rendern.

Ergebnis (in <startup>/runden/YYYY-MM-DD/): R-YYYYMMDD-NNN-budgetvorschlaege.html,
          AUSFUEHRUNGSPLAN_YYYYMMDD_BUDGET.json (Freigabe OFFEN; Dokumentation des Tages),
          je Adset ein Eintrag „Vorschlag“ in der Akte (Grund und Zahlen zum Entscheidungszeitpunkt)
          und eine kurze Markdown-Zusammenfassung auf stdout für den Chat (Kontosummen, größte Änderungen,
          Korrekturen gegenüber dem ursprünglichen Vorschlag, Link zum Bericht).
"""
import argparse
import html
import re
from collections import Counter
from datetime import date

import akte
from build_dataset import phase_text
from common import (ACCOUNTS, CURRENCY, CURRENCY_SIGN, ROOT, STARTUP, STARTUP_DIR, TW, datei, now_iso, read_json, runde,
                    write_json, write_text)

PLAN_EXTRAS = ("entscheidung", "umsetzung_meta")  # bleiben beim Neu-Rendern einer Zeile erhalten

MIN_BUDGET = STARTUP["mindestbudget"]  # aktive Adsets nie darunter; begründete Kürzung darunter = Pause
MIN_RULE = STARTUP.get("mindestbudget_regel") or "Mindestbudget laut startup.json"
ORDER = ["ERHOEHEN", "AKTIVIEREN", "SENKEN", "PAUSIEREN", "HALTEN"]
LABEL = {"ERHOEHEN": "Erhöhen", "AKTIVIEREN": "Aktivieren", "SENKEN": "Senken", "PAUSIEREN": "Pausieren",
         "HALTEN": "Halten"}
COUNT = {"ERHOEHEN": "erhöhen", "AKTIVIEREN": "aktivieren", "SENKEN": "senken", "PAUSIEREN": "pausieren",
         "HALTEN": "halten"}
CSS_CLASS = {"ERHOEHEN": "up", "AKTIVIEREN": "up", "SENKEN": "down", "PAUSIEREN": "off", "HALTEN": "hold"}
WINDOWS = [("y", "Gestern"), ("d3", "3 Tage"), ("d7", "7 Tage"), ("seit_aenderung", "Seit Änderung")]
MONTHS = ["JANUAR", "FEBRUAR", "MÄRZ", "APRIL", "MAI", "JUNI", "JULI", "AUGUST", "SEPTEMBER", "OKTOBER",
          "NOVEMBER", "DEZEMBER"]
E = html.escape

# Gestaltung: offene Tabellen, keine Aufklappfelder.
STYLE = """*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:25px}body{margin:0;background:#f5f7f9;color:#172330;font:15px/1.48 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1370px;margin:auto;padding:40px 36px 70px}a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}h1{font-size:34px;letter-spacing:-1px;line-height:1.15;margin:8px 0 12px}h2{font-size:20px;letter-spacing:-.4px;margin:0 0 16px}h2 span{font-size:13px;font-weight:500;color:#687480;margin-left:8px}.kicker{color:#60707d;font-size:12px;font-weight:750;letter-spacing:1.3px}.intro{max-width:960px;color:#536170}.status{display:inline-block;color:#835b13;background:#fff0cf;border:1px solid #ecd59e;border-radius:5px;padding:5px 10px;font-size:12px;font-weight:650}.status.ok{color:#1d6146;background:#e3f4ea;border-color:#b5dcc4}.cards{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:25px 0 18px}.card,.quick{background:#fff;border:1px solid #dce3e8;border-radius:10px;padding:24px}.card h2{margin-bottom:12px}.big{font-size:28px;font-weight:700;letter-spacing:-.7px}.sub{font-size:13px;color:#667380}.counts{margin-top:15px;padding-top:12px;border-top:1px solid #e8edf0;font-size:13px;color:#516171}.note{padding:15px 18px;background:#eaf1f4;border-radius:7px;font-size:13px;color:#3d5160;margin:12px 0}.note.warn{background:#fff4dc;color:#6b4d12}.focus{font-size:15px;margin:22px 0}.nav{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;margin:20px 0 24px;color:#315f7c}.quickgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start}table{width:100%;border-collapse:collapse;table-layout:fixed}th{text-align:left;font-size:12px;color:#60707f;padding:10px 9px;border-bottom:2px solid #dbe2e7}td{padding:11px 9px;border-bottom:1px solid #e8edf1;vertical-align:top}.quicktable{table-layout:auto;font-size:13px}.quicktable th:last-child,.quicktable td:last-child{text-align:right;white-space:nowrap;font-weight:650}.quicktable td{padding:8px 0}.quicktable a{display:flex;gap:10px}.quicktable small{color:#8a96a0;font-size:10px;line-height:20px;min-width:23px}.group td{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#6b7b89;padding:17px 0 7px!important;background:#fff}.up{color:#217052}.down{color:#a66a20}.off{color:#a34a51}.hold{color:#4e626e}.legend{margin:48px 0 18px;padding-top:26px;border-top:1px solid #d8e0e5;color:#516170;font-size:13px}.legend h2{font-size:25px;color:#182a38;margin-bottom:8px}.evidence{background:white;border:1px solid #dce3e8;border-radius:10px;padding:22px;margin:20px 0 30px}.evidence th{background:#f3f6f8}.evidence td{padding:17px 10px}.adtitle{display:flex;gap:8px}.adtitle em{font-style:normal;font-size:10px;color:#8b98a3;margin-top:4px;min-width:23px}.adtitle strong{font-size:14px}.reason{font-size:12px;color:#556572;margin:8px 0 8px 31px;line-height:1.5}.id{font-size:10px;color:#88959e;margin-left:31px;font-variant-numeric:tabular-nums}.budget strong{display:block;font-size:15px;white-space:nowrap}.budget small{font-size:10px}.metrics div{display:flex;justify-content:space-between;gap:7px;white-space:nowrap;font-size:12px}.metrics b{font-weight:700}.metrics span{font-size:10px;color:#536878}.metrics .tw{margin:4px 0 7px;color:#4d6380}.metrics small{display:block;font-size:10px;line-height:1.65;color:#788793}.footer{font-size:12px;color:#60727f;background:#eaf0f4;padding:22px;border-radius:8px}.footer p{margin:9px 0}tr:target{background:#fff7dc}footer{font-size:11px;color:#83919b;margin-top:28px} @media(max-width:1000px){main{padding:24px 16px}.quickgrid,.cards{grid-template-columns:1fr}.evidence{overflow-x:auto;padding:14px}.evidence table{min-width:1080px}.big{font-size:25px}} @media print{body{background:#fff}main{max-width:none;padding:0}.quickgrid{display:block}.quick{margin-bottom:20px}.nav{display:none}tr{break-inside:avoid}.evidence{overflow:visible}h2{break-after:avoid}}
.cards,.quickgrid{grid-template-columns:repeat(3,minmax(0,1fr))}.big{font-size:27px}.reason{line-height:1.5}.evidence{scroll-margin-top:14px}.id{overflow-wrap:anywhere}.note{line-height:1.6}.quicktable td{vertical-align:top}.metrics{font-variant-numeric:tabular-nums}.tw{margin-top:5px}.quicktable small{display:block}@media(max-width:1100px){.cards,.quickgrid{grid-template-columns:1fr}}"""


# ---------- Entscheidungen -> Planzeilen ----------

def decision(row, target_status, target_budget):
    if target_status == "PAUSED":
        return "HALTEN" if row["status"] == "PAUSED" else "PAUSIEREN"
    if row["status"] == "PAUSED":
        return "AKTIVIEREN"
    if target_budget > row["budget"]:
        return "ERHOEHEN"
    return "SENKEN" if target_budget < row["budget"] else "HALTEN"


def build_rows(dataset, decisions):
    by_id = {r["id"]: r for r in dataset["rows"]}
    errors, rows = [], []
    for d in decisions["entscheidungen"]:
        r = by_id.get(d["id"])
        if not r:
            errors.append(f"{d['id']}: nicht im Datenstand")
            continue
        if r["budget_ebene"] != "adset":
            errors.append(f"{d['id']}: kein Adset-Tagesbudget ({r['budget_ebene']}); nicht über diesen Plan steuerbar")
            continue
        if r.get("separat"):
            errors.append(f"{d['id']}: laut startup.json separat ({r['separat']}); nicht Teil des Plans")
            continue
        status, budget = d.get("ziel_status", "ACTIVE"), d.get("ziel_budget", r["budget"])
        if not d.get("grund"):
            errors.append(f"{d['id']}: Begründung fehlt")
        if status not in ("ACTIVE", "PAUSED"):
            errors.append(f"{d['id']}: ziel_status muss ACTIVE oder PAUSED sein")
            continue
        unchanged = status == r["status"] and budget == r["budget"]
        if status == "ACTIVE" and not unchanged and (budget is None or budget < MIN_BUDGET):
            errors.append(f"{d['id']}: aktives Zielbudget {budget} unter {MIN_BUDGET} {CURRENCY} ({MIN_RULE}: pausieren)")
            continue
        vorschlag = d.get("vorschlag") or {"budget": budget, "status": status}
        vorschlag.setdefault("grund", d.get("grund", ""))
        rows.append({**{k: r[k] for k in ("konto", "account_id", "id", "name", "campaign_id")},
                     "kurzname": d.get("kurzname") or r["name"], "budget": r["budget"], "status": r["status"],
                     "target_budget": budget, "target_status": status, "decision": decision(r, status, budget),
                     "reason": d.get("grund", ""), "phase": r.get("phase") or phase_text(r),
                     "rules": d.get("regeln", []),
                     # ursprünglicher Vorschlag des Skills mit Begründung; Korrekturen überschreiben ihn nie
                     "vorschlag": vorschlag,
                     **{k: d[k] for k in PLAN_EXTRAS if d.get(k)}})
    decided = {r["id"] for r in rows}
    for r in dataset["rows"]:
        if (r["effective_status"] == "ACTIVE" and r["budget_ebene"] == "adset" and not r.get("separat")
                and r["id"] not in decided):
            errors.append(f"{r['id']} ({r['name']}): aktives Adset ohne Entscheidung (auch Halten eintragen)")
    if errors:
        raise SystemExit("Entscheidungen unvollständig:\n  " + "\n  ".join(errors))
    order = list(ACCOUNTS)
    rows.sort(key=lambda x: (order.index(x["konto"]), x["name"] or ""))
    counters = Counter()
    for x in rows:
        counters[x["konto"]] += 1
        x["code"] = f"{ACCOUNTS[x['konto']]['prefix']}{counters[x['konto']]:02d}"
    return rows


def decisions_from_plan(plan):
    return {**plan.get("bericht", {}), "entscheidungen": [
        {"id": r["id"], "ziel_status": r["target_status"], "ziel_budget": r["target_budget"], "grund": r["reason"],
         "regeln": r["rules"], "kurzname": r.get("kurzname"), "vorschlag": r.get("vorschlag"),
         **{k: r[k] for k in PLAN_EXTRAS if r.get(k)}}
        for r in plan["rows"]]}


def akte_vorschlag(plan, dataset):
    """Je Planzeile ein Akteneintrag „Vorschlag“: Ist, Vorschlag des Skills, Grund, Regeln, Zahlen zum Zeitpunkt.
    Solange die Freigabe offen ist, ersetzt ein neues Rendern den Eintrag (noch keine Historie)."""
    by_id = {r["id"]: r for r in dataset["rows"]}
    fenster = dataset["fenster"]
    for r in plan["rows"]:
        d, v = by_id.get(r["id"], {}), r["vorschlag"]
        m, t = d.get("meta") or {}, d.get("tw") or {}

        def zahl(w):
            mm, tt = m.get(w), t.get(w)
            if not mm:
                return None
            tw = f", TW {num(tt['roas'])} / {buys(tt['kaeufe'])}" if tt else ", TW –"
            return f"{num(mm['roas'])} / {buys(mm['kaeufe'])} / {money(mm['spend'])}{tw}"

        zahlen = " · ".join(f"{label} {z}" for w, label in (("y", "gestern"), ("d3", "3 T"), ("d7", "7 T"),
                                                            ("seit_aenderung", "seit Änderung"))
                            if (z := zahl(w)))
        ziel = "AUS" if v["status"] == "PAUSED" else money(v["budget"])
        art = LABEL[decision(r, v["status"], v["budget"])]
        text = (f"**Ist {money(r['budget'])}{'' if r['status'] == 'ACTIVE' else ' (aus)'} → Vorschlag {ziel} · {art}**"
                f" · {', '.join(r['rules'])}\n\nGrund: {v.get('grund') or r['reason']}\n\n"
                f"Zahlen Meta ROAS / Käufe / Spend bis {fenster['y'][1]}: {zahlen or 'keine'}. "
                f"Link-CPC 3 T {money((m.get('d3') or {}).get('link_cpc'), 2)}. {r['phase']}\n\n"
                f"Bericht {plan['report_id']} · Plan {plan['change_id']}")
        akte.schreiben(r["account_id"], r["id"], r["name"],
                       akte.eintrag(plan["created_at"], f"Vorschlag · {plan['change_id']}", "vorschlag",
                                    plan["change_id"], text),
                       "vorschlag", plan["change_id"], replace=True)


def next_id(prefix, folder, run_day):
    stem = f"{prefix}-{run_day:%Y%m%d}-"
    used = [int(p.name[len(stem):len(stem) + 3]) for p in folder.rglob(stem + "*")]
    return f"{stem}{max(used, default=0) + 1:03d}"


# ---------- Formatierung ----------

def num(v, digits=2):
    if v is None:
        return "–"
    return f"{v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def money(v, digits=0):
    return "–" if v is None else f"{num(v, digits)} {CURRENCY_SIGN}"


def targets_text():
    """Zielwerte aus startup.json als Satz, z. B. „Meta-Ziel <ziel_roas>; Break-even Produkt A <wert>, Produkt B offen.“
    Ziel-ROAS ist eine Zahl für alle Produkte oder wie Break-even je Produkt: „Meta-Ziel Produkt A <wert>, …; …“."""
    z = STARTUP.get("zielwerte") or {}

    def per_product(values):
        return ", ".join(f"{k} {num(v)}" if v is not None else f"{k} offen" for k, v in values.items()) or "offen"

    goal = z.get("ziel_roas")
    goal = per_product(goal) if isinstance(goal, dict) else "offen" if goal is None else num(goal)
    return f"Meta-Ziel {goal}; Break-even {per_product(z.get('break_even') or {})}."


def buys(v):
    if v is None:
        return "–"
    n = num(v, 0) if float(v).is_integer() else num(v, 1)
    return f"{n} {'Kauf' if v == 1 else 'Käufe'}"


def span(von, bis):
    a, b = date.fromisoformat(von), date.fromisoformat(bis)
    if a == b:
        return f"{a:%d.%m.}"
    return f"{a:%d.}–{b:%d.%m.}" if a.month == b.month else f"{a:%d.%m.}–{b:%d.%m.}"


def target_text(r):
    return "AUS" if r["target_status"] == "PAUSED" else money(r["target_budget"])


# ---------- HTML-Bausteine ----------

def metric_cell(meta, tw, show_days=False):
    if not meta:
        return "<td class='metrics'><small>keine Änderung im Zeitraum bekannt</small></td>"
    tw_line = (f"<div class='tw'><b>TW {num(tw['roas'])}</b><span>{buys(tw['kaeufe'])}</span></div>" if tw
               else "<div class='tw'><b>TW –</b><span>keine Zuordnung</span></div>")
    days = f"<br>{span(meta['von'], meta['bis'])}" if show_days else ""
    return (f"<td class='metrics'><div><b>Meta {num(meta['roas'])}</b><span>{buys(meta['kaeufe'])}</span></div>"
            f"{tw_line}<small>{money(meta['spend'], 2)} Spend<br>Link-CPC {money(meta['link_cpc'], 2)}{days}</small></td>")


def separate_budgets(dataset, key):
    """Aktive Budgets eines Kontos außerhalb des Plans: Kampagnenbudgets (CBO, je Kampagne einmal gezählt)
    und Adsets, die startup.json als separat führt."""
    found = {}
    for r in dataset["rows"]:
        if r["konto"] != key or r["effective_status"] != "ACTIVE":
            continue
        if r["budget_ebene"] == "kampagne":
            found[r["campaign_id"]] = (r["campaign_name"] or r["campaign_id"], r["budget"] or 0)
        elif r.get("separat") and r["budget_ebene"] == "adset":
            found[r["id"]] = (r["separat"], r["budget"] or 0)
    return found


def card(key, rows, account, separate, hint):
    extra = sum(b for _, b in separate.values())
    before = sum(r["budget"] for r in rows if r["status"] == "ACTIVE") + extra
    after = sum(r["target_budget"] for r in rows if r["target_status"] == "ACTIVE") + extra
    sep_text = ("Inklusive separat " + ", ".join(f"{E(n)} {money(b)}" for n, b in separate.values())
                + " (unverändert)." if separate else "")
    sub = " · ".join(x for x in ("Geplantes aktives Tagesbudget", sep_text, E(hint or "")) if x)
    counts = Counter(r["decision"] for r in rows)
    count_text = " · ".join(f"{counts.get(k, 0)} {COUNT[k]}" for k in ORDER if k != "AKTIVIEREN" or counts.get(k))
    perf = ""
    if account:
        m, t = account["meta"], account.get("tw") or {}
        tw_of = lambda w: num((t.get(w) or {}).get("roas"))  # noqa: E731
        perf = (f"<p>Gestern <strong>Meta {num(m['y']['roas'])} · TW {tw_of('y')}</strong><br>"
                f"<span class='sub'>{buys(m['y']['kaeufe'])} Meta · {buys((t.get('y') or {}).get('kaeufe'))} TW<br>"
                f"3 Tage: Meta {num(m['d3']['roas'])} · TW {tw_of('d3')}<br>"
                f"7 Tage: Meta {num(m['d7']['roas'])} · TW {tw_of('d7')}</span></p>")
    return (f"<div class='card'><h2>{E(ACCOUNTS[key]['label'])} <span>{len(rows)} Adsets</span></h2>"
            f"<div class='big'>{money(before)} → {money(after)}</div>"
            f"<div class='sub'>{sub}</div>"
            f"<div class='counts'>{count_text}</div>{perf}</div>")


def quick(key, rows):
    changes = [r for r in rows if r["decision"] != "HALTEN"]
    body = []
    for k in ORDER[:-1]:
        group = [r for r in changes if r["decision"] == k]
        if group:
            body.append(f"<tr class='group'><td colspan='2'>{LABEL[k]}</td></tr>")
            body += [f"<tr><td><a href='#ad-{r['id']}'><small>{r['code']}</small>{E(r['kurzname'])}</a></td>"
                     f"<td class='{CSS_CLASS[k]}'>{money(r['budget'])} → {target_text(r)}</td></tr>" for r in group]
    if not changes:
        holds = "<br>".join(f"{E(r['kurzname'])}: {money(r['budget'])} halten" for r in rows)
        body.append(f"<tr><td colspan='2'>{holds}</td></tr>")
    return (f"<section class='quick'><h2>{E(ACCOUNTS[key]['label'])} <span>{len(changes)} Änderungen</span></h2>"
            f"<table class='quicktable'><thead><tr><th>Adset</th><th>Vorschlag / Tag</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></section>")


def evidence(title, anchor, rows, data_by_id, windows):
    head = "".join(f"<th>{label}<br><small>{span(*windows[w]) if w in windows else 'je Adset'}</small></th>"
                   for w, label in WINDOWS)
    trs = []
    for r in rows:
        d = data_by_id[r["id"]]
        phase = r.get("phase") or phase_text(d)
        cells = "".join(metric_cell(d["meta"].get(w), (d.get("tw") or {}).get(w), w == "seit_aenderung")
                        for w, _ in WINDOWS)
        cls = CSS_CLASS[r["decision"]]
        e, v = r.get("entscheidung") or {}, r.get("vorschlag") or {}
        korrektur = ""
        if e.get("art") == "korrigiert":
            skill = "AUS" if v.get("status") == "PAUSED" else money(v.get("budget"))
            korrektur = (f"<br><strong>Vorschlag Skill {skill} · Entscheidung {E(e.get('von') or '')}: "
                         f"{target_text(r)}</strong> – {E(e.get('grund') or 'Grund nicht genannt')}")
        trs.append(
            f"<tr id='ad-{r['id']}'><td><div class='adtitle'><em>{r['code']}</em>"
            f"<strong title='{E(r['name'] or '')}'>{E(r['kurzname'])}</strong></div>"
            f"<div class='reason'>{E(r['reason'])}{korrektur}<br><span class='sub'>{E(phase.strip())}</span></div>"
            f"<div class='id'>{r['id']} · {E(', '.join(r['rules']))}</div></td>"
            f"<td class='budget {cls}'><strong>{money(r['budget'])}</strong><strong>→ {target_text(r)}</strong>"
            f"<small>{LABEL[r['decision']]}</small></td>{cells}</tr>")
    cols = "".join(f"<col style='width:{w}'>" for w in ("34%", "10%", "14%", "14%", "14%", "14%"))
    return (f"<section class='evidence' id='{anchor}'><h2>{E(title)} <span>{len(rows)}</span></h2>"
            f"<table><colgroup>{cols}</colgroup><thead><tr><th>Adset & Begründung</th><th>Budget / Tag</th>{head}"
            f"</tr></thead><tbody>{''.join(trs)}</tbody></table></section>")


def render(dataset, plan, decisions):
    run_day = date.fromisoformat(dataset["lauftag"])
    windows = {w: tuple(v) for w, v in dataset["fenster"].items()}
    data_by_id = {r["id"]: r for r in dataset["rows"]}
    rows_by_key = {k: [r for r in plan["rows"] if r["konto"] == k] for k in ACCOUNTS}
    keys = [k for k in ACCOUNTS if rows_by_key[k]]
    rows = plan["rows"]
    counts = Counter(r["decision"] for r in rows)
    separate = {k: separate_budgets(dataset, k) for k in ACCOUNTS}
    extra = sum(b for s in separate.values() for _, b in s.values())
    before = sum(r["budget"] for r in rows if r["status"] == "ACTIVE") + extra
    after = sum(r["target_budget"] for r in rows if r["target_status"] == "ACTIVE") + extra
    delta = f" ({num((after - before) / before * 100, 1)} %)" if before else ""
    hints = decisions.get("kontohinweise", {})
    approved = plan["approval"]["status"] == "FREIGEGEBEN"
    status = (f"<span class='status ok'>Freigegeben von {E(plan['approval']['by'])}</span>" if approved
              else "<span class='status'>Budgetvorschläge · Freigabe offen</span>")
    if plan.get("test"):
        status = ("<span class='status' style='background:#fde2e2;border-color:#e8a5a5;color:#8a1f1f'>TESTLAUF</span> "
                  + status + "<div class='note warn' style='background:#fde2e2;color:#8a1f1f;font-size:15px'>"
                  "<strong>TESTLAUF mit erfundenen Daten.</strong> Nichts davon im Ads Manager umsetzen.</div>")
    notes = "".join(f"<div class='note'><strong>{E(n['titel'])}:</strong> {E(n['text'])}</div>"
                    for n in decisions.get("notizen", []))
    gaps = dataset["luecken"]
    gap_note = (f"<div class='note warn'><strong>Datenlücken:</strong> {E(' · '.join(gaps))}</div>" if gaps else "")
    nav = ["<a href='#quick'>Kurze Entscheidungsliste ↓</a>", "<a href='#zahlen'>Alle Zahlen & Gründe ↓</a>"]
    nav += [f"<a href='#{k}-halten'>{E(ACCOUNTS[k]['label'].split(' · ')[0])}: Halten ↓</a>" for k in keys
            if any(r["decision"] == "HALTEN" for r in rows_by_key[k])]
    sections = []
    for suffix, title, pick in (("aendern", "Änderungen", lambda r: r["decision"] != "HALTEN"),
                                ("halten", "Halten", lambda r: r["decision"] == "HALTEN")):
        for k in keys:
            chosen = [r for r in rows_by_key[k] if pick(r)]
            if chosen:
                sections.append(evidence(f"{ACCOUNTS[k]['label']} · {title}", f"{k}-{suffix}", chosen,
                                         data_by_id, windows))
    others = [r for r in dataset["rows"] if r["budget_ebene"] != "adset" and r["effective_status"] == "ACTIVE"]
    by_campaign = {}
    for r in others:
        by_campaign.setdefault((r["konto"], r["campaign_id"], r["campaign_name"], r["budget"]), []).append(r)
    other_items = " ".join(f"{E(ACCOUNTS[k]['label'])}: {E(name or cid)} <strong>{money(b)} gesamt</strong> "
                           f"für {len(v)} Adsets." for (k, cid, name, b), v in by_campaign.items())
    separate_items = " ".join(
        f"{E(ACCOUNTS[r['konto']]['label'])}: {E(r['separat'])} <strong>{money(r['budget'])}</strong> "
        f"(laut startup.json kein Verkaufs-Adset)." for r in dataset["rows"]
        if r.get("separat") and r["budget_ebene"] == "adset" and r["effective_status"] == "ACTIVE")
    separat = " ".join(x for x in (other_items, separate_items, E(decisions.get("separat", ""))) if x)
    tw = dataset.get("tw") or {}
    limits = "".join(f"<p>{E(g)}</p>" for g in decisions.get("grenzen", []))
    y, d3, d7 = windows["y"], windows["d3"], windows["d7"]
    meta_info = dataset["meta"]
    count_line = " · ".join(f"{counts.get(k, 0)} {COUNT[k]}" for k in ORDER if counts.get(k))
    used = learnings_text(rows)
    used_line = f"<p class='sub'>{E(used)}</p>" if used else ""
    month = MONTHS[run_day.month - 1]
    title = f"Budgetvorschläge · {run_day.day}. {month.capitalize()} · " + ", ".join(
        ACCOUNTS[k]["label"].split(" · ")[0] for k in keys)
    closing = ("Freigabe: " + E(plan["approval"]["wortlaut"] or "")) if approved else "Kein Budget-Go erteilt; keine Automation."
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<style>{STYLE}</style></head><body><main>
<div class="kicker">{E(STARTUP['name'].upper())} · MEDIA BUYING · {run_day.day}. {month} {run_day.year}</div>
<h1>{E(decisions.get('kopf') or 'Budgetvorschläge')}</h1>
{status}
<p class="intro">{len(rows)} aktive Adsets geprüft. Alle Vorschläge und Zahlen offen sichtbar.<br>Gestern: {span(*y)} · 3 Tage: {span(*d3)} · 7 Tage: {span(*d7)} · Budgets in {CURRENCY}.</p>
<div class="cards">{''.join(card(k, rows_by_key[k], dataset.get('konten', {}).get(k), separate[k], hints.get(k)) for k in keys)}</div>
<p class="focus"><strong>Gesamt:</strong> {money(before)} → <strong>{money(after)} täglich</strong>{delta}. {count_line}.</p>{used_line}
{gap_note}{notes}
<nav class="nav">{''.join(nav)}</nav>
<div class="quickgrid" id="quick">{''.join(quick(k, rows_by_key[k]) for k in keys)}</div>
<section class="legend" id="zahlen"><h2>Alle Zahlen und Gründe</h2>
<p>ROAS und Käufe je Quelle getrennt: Meta direkt aus der Marketing API, TW aus Triple Whale ({E(str(tw.get('modell', '–')))}, {E(str(tw.get('fenster', '–')))}). Spend und Link-CPC aus Meta in {CURRENCY}. Mehrtageswerte aus Summen, keine Tagesmittel. „–“ heißt nicht berechenbar oder keine Daten, nicht null. „Seit Änderung“ beginnt mit dem Änderungstag (Mischtag).</p></section>
{''.join(sections)}
<div class="footer">
<h2>Separat und nicht im Plan</h2><p>{separat or 'Keine aktiven Kampagnenbudgets außerhalb der Adset-Budgets.'}</p>
<h2>Datenstand und Grenzen</h2>
<p>{E(dataset['id'])} · erstellt {E(dataset['erstellt'][:16].replace('T', ' '))} · Fenster {span(*y)}, {span(*d3)}, {span(*d7)} · {span(*windows['heute'])} ist unvollständig und nicht Teil der Fenster. {E(targets_text())} Budgets sind eingestellte Tagesbudgets, keine Spendprognose.</p>
<p>Meta {E(str(meta_info.get('api_version')))}: Adset-Attributionseinstellung, Käufe {E(meta_info['kauf_action_type'])}, Link-CPC aus Link-Klicks (nicht CPC alle). Meta {CURRENCY}, TW {E(TW.get('waehrung') or 'Shop-Währung')}; Käufe und Umsatz beider Quellen nicht addieren, nicht automatisch den höheren Wert wählen. Kontokarten: alle Adsets mit Auslieferung im Zeitraum, auch inzwischen pausierte.</p>
{limits}
<p>Vor Umsetzung frischen Ist-Abgleich durchführen; zwischenzeitliche Änderungen bleiben erhalten. {closing}</p>
</div>
<footer>{E(plan['report_id'])} · {E(plan['change_id'])} · {len(rows)} Adsets · Budgetfreigabe {'erteilt' if approved else 'offen'}</footer>
</main></body></html>"""


TOP_CASES = 5  # Chat zeigt nur die größten Änderungen; die vollständige Liste steht im Bericht


def budget_effect(r):
    """Veränderung des aktiven Tagesbudgets durch eine Zeile (Pause = ganzes Budget)."""
    before = r["budget"] if r["status"] == "ACTIVE" else 0
    after = r["target_budget"] if r["target_status"] == "ACTIVE" else 0
    return abs((after or 0) - (before or 0))


def learnings_text(rows):
    """Wie oft bestätigte Learnings (IDs „L-NN“ in der Regelliste) Vorschläge geprägt haben, z. B.
    „Angewendete Learnings: L-01 ×3 · L-03 ×1“; leer, wenn keines."""
    used = Counter(rule for r in rows for rule in r.get("rules", []) if re.fullmatch(r"L-\d+", rule.strip()))
    return ("Angewendete Learnings: " + " · ".join(f"{k} ×{v}" for k, v in sorted(used.items()))) if used else ""


def corrected(r):
    v = r.get("vorschlag")
    return bool(v) and (v["status"], v["budget"]) != (r["target_status"], r["target_budget"])


def chat_summary(dataset, plan, out):
    """Kurz: Kontosummen, größte Änderungen, Korrekturen gegenüber dem Vorschlag, Link zum Bericht."""
    lines = ["**TESTLAUF – erfundene Daten, nichts im Ads Manager umsetzen.**", ""] if plan.get("test") else []
    lines += ["| Konto | Tagesbudget aktuell → Vorschlag | Änderungen |", "|---|---|---|"]
    for k in ACCOUNTS:
        rows = [r for r in plan["rows"] if r["konto"] == k]
        if not rows:
            continue
        extra = sum(b for _, b in separate_budgets(dataset, k).values())
        before = sum(r["budget"] for r in rows if r["status"] == "ACTIVE") + extra
        after = sum(r["target_budget"] for r in rows if r["target_status"] == "ACTIVE") + extra
        c = Counter(r["decision"] for r in rows)
        lines.append(f"| {ACCOUNTS[k]['label']} | {money(before)} → {money(after)} | "
                     + ", ".join(f"{c[x]} {COUNT[x]}" for x in ORDER if c.get(x)) + " |")
    changes = [r for r in plan["rows"] if r["decision"] != "HALTEN"]
    fixes = [r for r in plan["rows"] if corrected(r)]
    if fixes:
        lines += ["", "**Korrekturen gegenüber dem Vorschlag:**"]
        for r in fixes:
            v = r["vorschlag"]
            was = "AUS" if v["status"] == "PAUSED" else money(v["budget"])
            lines.append(f"- {r['code']} {r['kurzname']}: Vorschlag {was} → jetzt {target_text(r)}")
    top = sorted(changes, key=budget_effect, reverse=True)[:TOP_CASES]
    if top:
        lines += ["", "**Größte Änderungen:**"]
        lines += [f"- {r['code']} {r['kurzname']}: {money(r['budget'])} → {target_text(r)}" for r in top]
    if learnings_text(plan["rows"]):
        lines += ["", learnings_text(plan["rows"])]
    lines += ["", f"Alle {len(changes)} Änderungen mit Gründen und Zahlen im Bericht: "
                  f"`{out.relative_to(ROOT).as_posix()}`"]
    if any(r["status"] == "ACTIVE" and r["target_status"] == "ACTIVE" and r["target_budget"] < MIN_BUDGET
           for r in plan["rows"]):
        lines.append(f"Hinweis: Mindestens ein aktives Adset bleibt unter {MIN_BUDGET} {CURRENCY} ({MIN_RULE}); "
                     f"bitte mit {STARTUP['entscheider']} klären.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datenstand", required=True)
    ap.add_argument("--entscheidungen", help="nur beim ersten Rendern; danach aus dem Plan")
    args = ap.parse_args()
    dataset = read_json(datei(args.datenstand))
    run_day = date.fromisoformat(dataset["lauftag"])
    plan_path = runde(run_day) / f"AUSFUEHRUNGSPLAN_{run_day:%Y%m%d}_BUDGET.json"
    old = read_json(plan_path) if plan_path.exists() else None
    if old and old["approval"]["status"] != "OFFEN" and args.entscheidungen:
        raise SystemExit(f"{plan_path.name} ist bereits freigegeben; Entscheidungen nicht mehr überschreiben.")
    if args.entscheidungen:
        decisions = read_json(args.entscheidungen)
    elif old:
        decisions = decisions_from_plan(old)
    else:
        raise SystemExit("Weder --entscheidungen noch ein vorhandener Plan.")
    rows = build_rows(dataset, decisions)
    report_id = (old or {}).get("report_id") or next_id("R", runde(run_day), run_day)
    # ID des Ausführungsplans (A-…), gleiche Nummer wie der Bericht; steht in Akten und Abgleich
    change_id = (old or {}).get("change_id") or report_id.replace("R-", "A-", 1)
    plan = old if old and old["approval"]["status"] != "OFFEN" else {
        "created_at": (old or {}).get("created_at") or now_iso(), "test": bool(dataset.get("test")),
        "lauftag": dataset["lauftag"],
        "change_id": change_id, "report_id": report_id,
        "dataset_id": dataset["id"], "status": "VORGESCHLAGEN",
        "rulebook": f"{STARTUP_DIR.name}/regeln/MEDIA_BUYING_REGELN.md (Stand laut Datei)",
        "approval": {"status": "OFFEN", "by": None, "at": None, "wortlaut": None},
        "execution": {"weg": None, "status": "NICHT_AUSGEFUEHRT"}, "verification_file": None,
        "rollback": "Vorherwerte budget/status je Zeile. Rücknahme nur nach neuer Freigabe.",
        "bericht": {k: decisions[k] for k in ("auftrag", "kopf", "notizen", "kontohinweise", "separat", "grenzen")
                    if k in decisions},
        "rows": rows}
    if old and old.get("ausserhalb_plan") and plan is not old:
        plan["ausserhalb_plan"] = old["ausserhalb_plan"]  # Abgleich mit Meta bleibt erhalten
    write_json(plan_path, plan)
    if plan["approval"]["status"] == "OFFEN":
        akte_vorschlag(plan, dataset)
    out = write_text(runde(run_day) / f"{plan['report_id']}-budgetvorschlaege.html",
                     render(dataset, plan, plan.get("bericht", {})))
    print(chat_summary(dataset, plan, out))
    print(f"\nPlan {plan['change_id']}: {plan_path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
