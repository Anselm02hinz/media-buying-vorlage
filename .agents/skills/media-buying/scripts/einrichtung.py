"""Prüft die Einrichtung und nennt den nächsten Schritt. Nur lesend: lokale Dateien und GET-Aufrufe.

    python einrichtung.py [--kampagnen]

Zugangsdaten erscheinen nie in der Ausgabe, nur „gesetzt“ oder „fehlt“. Der Stand der Einrichtung ergibt sich
jedes Mal neu aus den Prüfungen; so lässt sich die Einrichtung in jedem neuen Chat fortsetzen.
Ablauf für die KI: references/einrichtung.md · Klickwege für Menschen: ANLEITUNG.md im Repository-Root.
"""
import argparse
import json
import os
import re
from datetime import datetime

from common import (ACCOUNTS, FIXTURE, META_API_VERSION, ROOT, STARTUP, STARTUP_DIR, TEST_MODE, TW, TZ, ApiError,
                    http_json, read_json, token_erinnerung)
from fetch_meta import graph

PLATZHALTER_NAME = "Vorname Nachname"
PLATZHALTER_KONTO = "100000000000001"
PLATZHALTER_PRODUKT = "Produkt A"
VERKAUFSZIELE = ("OUTCOME_SALES", "CONVERSIONS", "PRODUCT_CATALOG_SALES")
KONTOSTATUS = {1: "aktiv", 2: "deaktiviert", 3: "Zahlung offen", 7: "in Prüfung", 9: "Kulanzzeit", 101: "geschlossen"}
TW_TEST = "https://api.triplewhale.com/api/v2/users/api-keys/me"
# Kerndateien; die mit Punkt am Anfang fehlen nach einem Upload leicht, weil sie versteckt sind
KERN = ("AGENTS.md", "ANLEITUNG.md", "README.md", ".gitignore", ".env.example",
        ".agents/skills/media-buying/SKILL.md", ".agents/skills/media-buying/references/einrichtung.md",
        ".agents/skills/media-buying/references/regelvorlagen.md")
# Schritte der Einrichtung in ihrer Reihenfolge: (Schlüssel, Name, was zu tun ist)
SCHRITTE = [
    ("upload", "Upload", "Fehlende Dateien nachladen: versteckte Dateien einblenden und erneut hochladen "
                         "(ANLEITUNG.md, A2 und A3)."),
    ("meta", "Meta-Zugang", "Meta-Token anlegen, in der Umgebung als META_ACCESS_TOKEN eintragen und speichern "
                            "(ANLEITUNG.md, B1 und B3; Claude Code: B3a), danach einen neuen Chat starten."),
    ("internet", "Internetzugang", "graph.facebook.com (mit Triple Whale auch api.triplewhale.com) als erlaubte "
                                   "Domain eintragen: Codex unter „Additional allowed domains“, dann Republish "
                                   "(ANLEITUNG.md, B3); Claude Code im Web unter „Network access“ → „Custom“ (B3a). "
                                   "Danach einen neuen Chat starten."),
    ("konten", "Werbekonten", "Werbekonten aus der Liste auswählen; die KI trägt sie in startup.json ein."),
    ("angaben", "Angaben zum Startup", "Fragen zum Startup beantworten (Fragenblock in references/einrichtung.md)."),
    ("regeln", "Media-Buying-Regeln", "Startregeln festlegen: Die KI schlägt sie vor (references/regelvorlagen.md), "
                                      "der Entscheider bestätigt oder passt an."),
    ("triple_whale", "Triple Whale", "Triple-Whale-Key anlegen, in der Umgebung als TRIPLEWHALE_API_KEY eintragen und "
                                     "speichern (ANLEITUNG.md, B2 und B3; Claude Code: B3a), danach einen neuen Chat "
                                     "starten."),
    ("testdaten", "Testdaten", "Testdaten-Schlüssel an die Konten anpassen (macht die KI)."),
    ("bestaetigung", "Bestätigung", "Alle Werte vom Entscheider bestätigen lassen, dann \"beispiel\": false setzen; "
                                    "danach PR erstellen und mergen (ANLEITUNG.md, B4)."),
]


def befund(status, schritt, text):
    """status: OK, FEHLT (hält den Schritt auf), OFFEN (bewusst unbekannt), HINWEIS."""
    return {"status": status, "schritt": schritt, "text": text}


def pruefe_dateien(root):
    missing = [p for p in KERN if not (root / p).exists()]
    out = [befund("FEHLT", "upload", f"Datei fehlt: {p}") for p in missing]
    if (root / ".env").exists():
        out.append(befund("HINWEIS", "upload", ".env liegt im Repository-Ordner: nur lokal nutzen, nie hochladen; "
                                               "in Codex gehören die Werte in die Umgebungsvariablen."))
    return out or [befund("OK", "upload", "Alle Kerndateien vorhanden")]


def pruefe_stammdaten(startup, ordnername):
    out = []
    if not startup.get("name") or startup["name"] == "Beispiel-Startup":
        out.append(befund("FEHLT", "angaben", "Name des Startups fehlt (noch Beispielwert)"))
    for rolle in ("entscheider", "systemverantwortlich"):
        if startup.get(rolle) in (None, "", PLATZHALTER_NAME):
            out.append(befund("FEHLT", "angaben", f"{rolle}: Name fehlt (noch Beispielwert)"))
    for key, acc in startup.get("konten", {}).items():
        if str(acc.get("id")) == PLATZHALTER_KONTO:
            out.append(befund("FEHLT", "konten", f"Konto {key!r}: noch die Beispiel-ID"))
    out += pruefe_zielwerte(startup.get("zielwerte") or {})
    if startup.get("mindestbudget_regel") in (None, "", "OFFEN"):
        out.append(befund("OFFEN", "angaben", f"Mindestbudget {startup.get('mindestbudget')}: ohne Regel-ID (OFFEN)"))
    tw = startup.get("triple_whale") or {}
    if tw.get("aktiv") and not (tw.get("shop_domain") or os.environ.get("TRIPLEWHALE_SHOP_DOMAIN")):
        out.append(befund("FEHLT", "angaben", "Triple Whale aktiv, aber shop_domain fehlt"))
    if ordnername == "startup":
        out.append(befund("HINWEIS", "angaben", "Startup-Ordner heißt noch startup/; nach dem Startup umbenennen"))
    if startup.get("beispiel"):
        out.append(befund("FEHLT", "bestaetigung", "startup.json enthält noch Beispielwerte (\"beispiel\": true); "
                                                   "nur Testläufe möglich"))
    if not any(b["status"] == "FEHLT" for b in out):
        out.insert(0, befund("OK", "angaben", "Stammdaten vollständig"))
    return out


def ist_zahl(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def pruefe_zielwerte(z):
    """Break-even je Produkt; Ziel-ROAS als eine Zahl für alle Produkte oder je Produkt mit denselben Produktnamen
    ({"Produkt A": 2.2}). Ein Ziel-ROAS unter dem Break-even eines Produkts ist vermutlich ein Versehen."""
    out, be, ziel = [], z.get("break_even") or {}, z.get("ziel_roas")
    je_produkt = ziel if isinstance(ziel, dict) else None
    produkte = [p for p in dict.fromkeys([*be, *(je_produkt or {})]) if p != PLATZHALTER_PRODUKT]
    for name, werte in (("Break-even", be), ("Ziel-ROAS", je_produkt)):
        if werte is None:
            continue
        if PLATZHALTER_PRODUKT in werte:
            out.append(befund("FEHLT", "angaben", f"{name}: Produkte sind noch Beispielwerte"))
        for p in produkte:
            if werte.get(p) is None:
                out.append(befund("OFFEN", "angaben", f"{name} {p}: OFFEN"))
            elif not ist_zahl(werte[p]):
                out.append(befund("FEHLT", "angaben", f"{name} {p}: {werte[p]!r} ist keine Zahl"))
    if je_produkt is None and ziel is None:
        out.append(befund("OFFEN", "angaben", "Ziel-ROAS: OFFEN"))
    elif je_produkt is None and not ist_zahl(ziel):
        out.append(befund("FEHLT", "angaben", f"Ziel-ROAS: {ziel!r} ist weder eine Zahl noch eine Angabe je Produkt"))
    for p in produkte:
        ziel_p = je_produkt.get(p) if je_produkt is not None else ziel
        if ist_zahl(ziel_p) and ist_zahl(be.get(p)) and ziel_p < be[p]:
            tipp = "" if je_produkt is not None else "; ggf. Ziel-ROAS je Produkt festlegen"
            out.append(befund("HINWEIS", "angaben", f"{p}: Ziel-ROAS {ziel_p:g} liegt unter Break-even {be[p]:g}"
                                                    f"{tipp}"))
    return out


def pruefe_regeln(path):
    """Mindestens eine Regel: Abschnitt „## MB-NNNN“ außerhalb von Codeblöcken (dort steht nur das Format)."""
    if not path.exists():
        return [befund("FEHLT", "regeln", f"{path.name} fehlt")]
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    n = len(re.findall(r"^## MB-\d{4}\b", text, flags=re.M))
    if not n:
        return [befund("FEHLT", "regeln", "Noch keine Media-Buying-Regeln; ohne Regeln hat der Skill keine "
                                          "Entscheidungsgrundlage")]
    return [befund("OK", "regeln", f"{n} Media-Buying-Regeln festgelegt")]


def pruefe_token(startup, heute, token_gesetzt):
    """Erinnerung zum Erneuern des Meta-Tokens (startup.json `meta_token`)."""
    if not token_gesetzt:
        return []
    if not (startup.get("meta_token") or {}).get("erstellt"):
        return [befund("OFFEN", "meta", "Erstelldatum des Meta-Tokens fehlt (startup.json meta_token.erstellt); "
                                        "ohne Datum keine Erinnerung zum Erneuern")]
    text = token_erinnerung(startup, heute)
    return [befund("HINWEIS", "meta", text)] if text else [befund("OK", "meta", "Meta-Token noch nicht zu erneuern")]


def pruefe_testdaten(konten, fixture):
    if not fixture.exists():
        return [befund("FEHLT", "testdaten", f"{fixture.name} fehlt")]
    missing = [k for k in konten if k not in read_json(fixture).get("konten", {})]
    if missing:
        return [befund("FEHLT", "testdaten", f"Testdaten ohne Eintrag für Konto: {', '.join(missing)}")]
    return [befund("OK", "testdaten", "Testdaten passen zu den Konten")]


def pruefe_zugaenge(env, tw_aktiv, test_mode):
    out = []
    modus = env.get("MEDIA_BUYING_MODUS", "").strip().lower()
    if modus not in ("", "test"):
        out.append(befund("HINWEIS", "meta", f"MEDIA_BUYING_MODUS={modus!r} unbekannt; erlaubt: leer oder test"))
    if env.get("META_WRITE_ENABLED") == "1":
        out.append(befund("HINWEIS", "meta", "Schreibzugriff ist eingeschaltet (META_WRITE_ENABLED=1); das dürfen nur "
                                             "Entscheider oder Systemverantwortlicher, für die Einrichtung 0 lassen"))
    else:
        out.append(befund("OK", "meta", "Schreibzugriff gesperrt (META_WRITE_ENABLED nicht 1)"))
    if test_mode:
        return out + [befund("HINWEIS", "meta", "Testmodus (MEDIA_BUYING_MODUS=test): Zugänge werden nicht geprüft")]
    out.append(befund("OK", "meta", "META_ACCESS_TOKEN gesetzt") if env.get("META_ACCESS_TOKEN")
               else befund("FEHLT", "meta", "META_ACCESS_TOKEN fehlt"))
    if tw_aktiv:
        out.append(befund("OK", "triple_whale", "TRIPLEWHALE_API_KEY gesetzt") if env.get("TRIPLEWHALE_API_KEY")
                   else befund("FEHLT", "triple_whale", "TRIPLEWHALE_API_KEY fehlt"))
    return out


def netzfehler(error):
    """Meta und Triple Whale antworten bei eigenen Fehlern mit JSON; alles andere heißt: Ziel nicht erreichbar."""
    text = str(error)
    return "HTTP" not in text or not any(k in text for k in ('"error"', '"message"', '"code"'))


def pruefe_meta(token, version):
    """(Befunde, Konten des Tokens oder None)."""
    try:
        konten = graph("me/adaccounts", token, version, limit=200,
                       fields="account_id,name,currency,timezone_name,account_status")
    except ApiError as e:
        if netzfehler(e):
            return [befund("FEHLT", "internet", "graph.facebook.com nicht erreichbar: Internetzugang fehlt")], None
        if '"code":190' in str(e).replace(" ", ""):
            return [befund("FEHLT", "meta", "Meta-Token ungültig oder abgelaufen; neuen Token erzeugen")], None
        return [befund("FEHLT", "meta", f"Meta-Abruf fehlgeschlagen: {e}")], None
    if not konten:
        return [befund("FEHLT", "meta", "Der Token sieht keine Werbekonten: Konten dem Systemnutzer zuweisen")], []
    out = [befund("OK", "internet", "graph.facebook.com erreichbar"),
           befund("OK", "meta", f"Meta-Token gültig, {len(konten)} Werbekonten freigegeben")]
    try:
        rechte = {p.get("permission") for p in graph("me/permissions", token, version) if p.get("status") == "granted"}
    except ApiError:
        rechte = None
    if rechte is None:
        out.append(befund("HINWEIS", "meta", "Rechte des Tokens nicht prüfbar"))
    elif "ads_management" in rechte:
        out.append(befund("HINWEIS", "meta", "Token hat ads_management (Schreibrecht); für den Start reicht ads_read"))
    return out, konten


def vergleiche_konten(konten, gesehen, zeitzone, waehrung):
    by_id = {str(a.get("account_id") or a.get("id", "").replace("act_", "")): a for a in gesehen}
    out = []
    for key, acc in konten.items():
        acc_id = str(acc.get("id"))
        if acc_id == PLATZHALTER_KONTO:
            continue
        a = by_id.get(acc_id)
        if not a:
            out.append(befund("FEHLT", "konten", f"Konto {key!r} ({acc_id}) nicht freigegeben: im Business Manager "
                                                 "dem Systemnutzer zuweisen"))
            continue
        if a.get("currency") and a["currency"] != waehrung:
            out.append(befund("FEHLT", "angaben", f"Konto {key!r}: Währung {a['currency']} laut Meta, "
                                                  f"{waehrung} laut startup.json"))
        if a.get("timezone_name") and a["timezone_name"] != zeitzone:
            out.append(befund("FEHLT", "angaben", f"Konto {key!r}: Zeitzone {a['timezone_name']} laut Meta, "
                                                  f"{zeitzone} laut startup.json"))
        if a.get("account_status") not in (None, 1):
            out.append(befund("HINWEIS", "konten", f"Konto {key!r}: Status "
                                                   f"{KONTOSTATUS.get(a['account_status'], a['account_status'])}"))
    if not out and any(str(a.get("id")) != PLATZHALTER_KONTO for a in konten.values()):
        out.append(befund("OK", "konten", "Konten aus startup.json freigegeben, Währung und Zeitzone passen"))
    return out


def pruefe_tw(key):
    try:
        http_json("GET", TW_TEST, headers={"x-api-key": key, "Accept": "application/json"})
    except ApiError as e:
        if netzfehler(e):
            return [befund("FEHLT", "internet", "api.triplewhale.com nicht erreichbar: Internetzugang fehlt")]
        return [befund("FEHLT", "triple_whale", "Triple-Whale-Key ungültig oder ohne Leserecht")]
    return [befund("OK", "triple_whale", "Triple-Whale-Key gültig")]


def vorschlag_separat(kampagnen):
    """Aktive Kampagnen ohne Verkaufsziel (z. B. Follower, Reichweite) als Kandidaten für `separat`."""
    return [k for k in kampagnen if k.get("objective") not in VERKAUFSZIELE]


def naechster_schritt(befunde):
    """(Nummer, Name, was zu tun ist) des ersten Schritts mit FEHLT; (None, …) wenn alles bereit ist."""
    offen = {b["schritt"] for b in befunde if b["status"] == "FEHLT"}
    for i, (key, name, todo) in enumerate(SCHRITTE, 1):
        if key in offen:
            return i, name, todo
    return None, "Bereit", ("Erster Lauf: „Mach mein Media Buying für heute“. Danach PR erstellen und mergen.")


def kampagnen_ausgeben(ids, token, version):
    filt = json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}])
    for acc_id in ids:
        try:
            camps = graph(f"act_{acc_id}/campaigns", token, version, limit=200, filtering=filt,
                          fields="id,name,objective,effective_status,daily_budget")
        except ApiError as e:
            print(f"  act_{acc_id}: Kampagnen nicht abrufbar ({e})")
            continue
        print(f"\nAktive Kampagnen act_{acc_id}: {len(camps)}")
        for c in camps:
            print(f"  {c.get('id')} · {c.get('name')} · {c.get('objective')}")
        for c in vorschlag_separat(camps):
            print(f"  Vorschlag separat (kein Verkaufsziel): {c.get('id')} · {c.get('name')} · {c.get('objective')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kampagnen", action="store_true", help="aktive Kampagnen je Konto mit Vorschlag für separat")
    args = ap.parse_args()
    env, version = os.environ, META_API_VERSION
    gesehen, token = None, env.get("META_ACCESS_TOKEN")
    befunde = (pruefe_dateien(ROOT) + pruefe_stammdaten(STARTUP, STARTUP_DIR.name)
               + pruefe_regeln(STARTUP_DIR / "regeln" / "MEDIA_BUYING_REGELN.md")
               + pruefe_testdaten(ACCOUNTS, FIXTURE) + pruefe_zugaenge(env, TW["aktiv"], TEST_MODE)
               + pruefe_token(STARTUP, datetime.now(TZ).date(), bool(token) and not TEST_MODE))
    if token and not TEST_MODE:
        b, gesehen = pruefe_meta(token, version)
        befunde += b
        if gesehen:
            befunde += vergleiche_konten(ACCOUNTS, gesehen, STARTUP["zeitzone"], STARTUP["waehrung"])
    if TW["aktiv"] and env.get("TRIPLEWHALE_API_KEY") and not TEST_MODE:
        befunde += pruefe_tw(env["TRIPLEWHALE_API_KEY"])
    print(f"Einrichtung · {STARTUP.get('name')} · Startup-Ordner {STARTUP_DIR.name}/")
    for key, name, _ in SCHRITTE:
        for b in (b for b in befunde if b["schritt"] == key):
            print(f"  {b['status']:<8}{name}: {b['text']}")
    if gesehen:
        print("\nWerbekonten, die der Token sieht:")
        for a in gesehen:
            status = KONTOSTATUS.get(a.get("account_status"), a.get("account_status"))
            print(f"  {a.get('account_id')} · {a.get('name')} · {a.get('currency')} · {a.get('timezone_name')} · {status}")
    if args.kampagnen and gesehen:
        echte = [str(a["id"]) for a in ACCOUNTS.values() if str(a["id"]) != PLATZHALTER_KONTO]
        kampagnen_ausgeben(echte or [str(a.get("account_id")) for a in gesehen], token, version)
    offen = {b["schritt"] for b in befunde if b["status"] == "FEHLT"}
    print(f"\nTestlauf möglich: {'nein' if 'testdaten' in offen else 'ja'}")
    nr, name, todo = naechster_schritt(befunde)
    print(f"Stand: {'alles bereit' if nr is None else f'Schritt {nr} von {len(SCHRITTE)} ({name})'}")
    print(f"Nächster Schritt: {todo}")


if __name__ == "__main__":
    main()
