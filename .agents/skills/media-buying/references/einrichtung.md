# Geführte Einrichtung

Ablauf für die KI, wenn ein neues Startup den Skill einrichtet. Die Klickwege für Menschen stehen in `ANLEITUNG.md` im Repository-Root (Teil A: bis Codex läuft; Teil B: Meta, Triple Whale, Codex-Umgebung, PR). Diese Datei sagt, was die KI selbst erledigt, wann sie den Media Buyer braucht und was sie nie tut.

**Wann:** `<startup>/startup.json` enthält `"beispiel": true`, oder jemand sagt „Richte den Skill ein“, „Weiter mit der Einrichtung“, „Einrichtung“ oder „Setup“. Fehlt der Ordner `.agents/skills/media-buying/`, ist der Upload unvollständig (siehe `AGENTS.md`).

**Kern der Einrichtung ist das Mandat des Startups:** sein Ziel in eigenen Worten ([mandat.md](mandat.md)). Ohne Ziel hat der Skill keine Entscheidungsgrundlage. Starre Regeln braucht es nicht: Wie das Ziel erreicht wird, entscheidet der Skill je Runde nach Fachwissen ([fachwissen.md](fachwissen.md)), wie ein Media-Buying-Dienstleister; der Entscheider gibt frei oder korrigiert. Das früh im Gespräch ankündigen, damit der Entscheider sich darauf einstellt.

## Grundsätze

- **Stand prüfen, nicht erinnern:** Jeder Einrichtungs-Chat beginnt mit `python3 .agents/skills/media-buying/scripts/einrichtung.py` (unter Windows siehe `CLAUDE.md`). Es zeigt, was fertig ist, was fehlt und den **nächsten Schritt**. Danach richten.
- **Für Anfänger:** ein Schritt pro Nachricht, kurze Sätze, keine Fachbegriffe ohne Erklärung, Button-Namen wie in `ANLEITUNG.md` Teil B. Auf „erledigt“ oder eine Frage warten. Nach jedem Schritt kurz bestätigen, was jetzt geht.
- **Klickwege nicht erfinden:** aus `ANLEITUNG.md` Teil B übernehmen. Weicht die Oberfläche ab, den Media Buyer beschreiben lassen, was er sieht.
- **Zugangsdaten nie im Chat:** Token und Keys gehören nur in die Umgebung unter „Environment variables“ (Codex B3, nicht unter „HTTP secrets“; Claude Code im Web B3a, nicht unter „Network secrets“; lokal `.env`), weil die Skripte den Wert selbst brauchen. Nie danach fragen, nie ausgeben, nie in Dateien schreiben. Fügt jemand einen Token in den Chat ein: nicht verwenden, nicht speichern, darauf hinweisen, ihn in Meta neu zu erzeugen und nur in der Umgebung einzutragen.
- **Internetzugang:** Die Umgebung muss `graph.facebook.com` und, mit Triple Whale, `api.triplewhale.com` erreichen. Codex: „Additional allowed domains“ (B3). Claude Code im Web: „Network access“ → „Custom“, „Allowed domains“ (B3a); die Standardstufe „Trusted“ sperrt beide. Claude Code lokal: nur bei eingeschalteter Sandbox nötig (B3a). Die Einstellung trägt der Media Buyer ein, nicht die KI.
- **Geänderte Umgebung gilt erst nach „Republish“ (Codex) bzw. „Save changes“ (Claude Code) und in einem neuen Chat.** Nach B3 bzw. B3a immer: „Starte einen neuen Chat mit: Weiter mit der Einrichtung.“
- **Bestätigen lässt der Entscheider:** `startup.json`, Profil `README.md` und Mandat sind Entscheidungsgrundlagen (`AGENTS.md`). Ist die Person im Chat nicht der Entscheider, braucht es dessen Ja.

## Was die KI allein macht

- `einrichtung.py` ausführen und das Ergebnis in einfachen Worten zusammenfassen; mit `--kampagnen` die aktiven Kampagnen listen.
- Tests ausführen: `python3 -m unittest discover .agents/skills/media-buying/tests`. Schlagen sie fehl: melden, nicht weitermachen.
- Testlauf auf Wunsch, ohne Zugänge: den Ablauf aus `SKILL.md` mit `MEDIA_BUYING_MODUS=test` vor jedem Befehl (z. B. `MEDIA_BUYING_MODUS=test python3 …/fetch_meta.py`). Er zeigt erfundene Daten und die Chat-Zusammenfassung des Berichts.
- Konten, Währung und Zeitzone aus Meta übernehmen; Kampagnen ohne Verkaufsziel als `separat` vorschlagen.
- Das Ziel mit dem Entscheider formulieren ([mandat.md](mandat.md)); keine Regeln, Schwellen oder Prozentstaffeln vorschlagen.
- Nach Bestätigung alle Dateien schreiben (Chat 2, Schritt 7), den Startup-Ordner umbenennen, prüfen.

## Ablauf

### Beim Anlegen der Codex-Umgebung (vor „Publish“)

Codex richtet die Umgebung in einem eigenen Gespräch ein. Dort nur sicherstellen, dass `python3` läuft, Zeitzonen da sind (`python3 -c "import zoneinfo; zoneinfo.ZoneInfo('Europe/Berlin')"`) und die Tests grün sind. Keine Pakete nötig (nur Standardbibliothek). Keine Einrichtungsfragen stellen; die geführte Einrichtung beginnt im ersten Chat nach dem Veröffentlichen.

### Chat 1 · Vorbereitung (noch ohne Zugänge, nichts zu sichern)

1. `einrichtung.py`. Fehlt etwas beim **Upload**: anleiten nach `ANLEITUNG.md` A2 und A3 (fehlende Dateien einzeln nachladen), dann neuer Chat.
2. Tests ausführen. Kurz erklären, was der Skill tut (`ANLEITUNG.md`, „Was ist das?“).
3. Anbieten: „Möchtest du zuerst einen Testlauf mit erfundenen Daten sehen?“ Wenn ja: Testlauf (oben). Seine Dateien müssen nicht gesichert werden.
4. Fragen: „Hast du Admin-Zugang zum Meta Business Manager eurer Werbekonten?“ Wenn nein: Wer hat ihn? Diese Person macht B1.
5. **Meta-Token** nach `ANLEITUNG.md` B1, Schritt für Schritt. Am Ende hat der Media Buyer den Token kopiert, aber nicht in den Chat eingefügt. Ablauf „Nie“; dafür eine Kalender-Erinnerung in 6 Monaten zum Erneuern empfehlen (B6). Das Erstellungsdatum merkt sich der Media Buyer für Chat 2.
6. Fragen: „Nutzt ihr Triple Whale?“ Wenn ja: **Triple-Whale-Key** nach B2.
7. **Codex-Umgebung** nach B3: unter „Environment variables“ `META_ACCESS_TOKEN` (ggf. `TRIPLEWHALE_API_KEY`, `TRIPLEWHALE_SHOP_DOMAIN`), unter „Additional allowed domains“ `graph.facebook.com` (ggf. `api.triplewhale.com`), dann „Republish“. `META_WRITE_ENABLED` nicht anlegen. In Claude Code stattdessen nach B3a: im Web „Environment variables“ und „Network access“ → „Custom“ mit denselben Domains, dann „Save changes“; lokal `.env` und, nur mit Sandbox, die Domains erlauben.
8. „Starte jetzt einen neuen Chat mit: **Weiter mit der Einrichtung**.“

### Chat 2 · Einrichten (mit Zugängen)

1. `einrichtung.py`. Bei FEHLT in Meta-Zugang oder Internetzugang: zurück zu B1 bzw. B3 (Claude Code: B3a). Bei FEHLT in **Werbekonto** (Token sieht keins): fragen, ob es schon ein Werbekonto gibt; wenn ja, B1 Schritt 9 (dem Systemnutzer zuweisen), wenn nein, zuerst ein Werbekonto im Business-Portfolio anlegen lassen.
2. **Konten:** die Liste der Werbekonten zeigen und fragen, welche zum Auftrag gehören. Je Konto: Kurzname (Kleinbuchstaben, z. B. `haupt`), Anzeigename, Meta-Name, Präfix (A, B, …). Währung und Zeitzone aus Meta. Ein Konto mit Status „deaktiviert“, „Zahlung offen“ oder „geschlossen“ liefert nicht aus; das zuerst klären lassen.
3. **Kampagnen:** `einrichtung.py --kampagnen` zeigt je aktiver Kampagne Ziel und Budgetebene. Die Vorschläge für `separat` zeigen und bestätigen lassen. Der Skill steuert bisher nur **Adsets mit eigenem Tagesbudget**: Gibt es nur Kampagnen mit Kampagnen- oder Laufzeitbudget (z. B. Advantage+) oder gar keine aktiven Kampagnen, das offen sagen; dann hat der Skill noch nichts zu steuern, bis es eine Verkaufskampagne mit Adset-Budgets gibt. Nach dem Schreiben der Konten (Schritt 7) prüft `einrichtung.py` das unter „Kampagnen“ und „Kaufmessung“ selbst: Hat ein Konto in 28 Tagen Spend, aber keinen gemessenen Kauf, ist die Messung (Pixel, Conversions API) zuerst zu klären.
4. **Fragenblock** in einer Nachricht, nummeriert; jede Antwort darf „weiß ich nicht“ sein (dann OFFEN, nichts schätzen):
   1. Wie heißt euer Startup?
   2. Wer entscheidet über die Budgets (Entscheider)? Wer betreut das System technisch (Systemverantwortlicher)? Das darf dieselbe Person sein.
   3. Welche Produkte bewerbt ihr? Ab welchem ROAS ist jedes Produkt profitabel (Break-even)?
   4. Welchen ROAS strebt ihr an (Ziel-ROAS)? Einen für alle Produkte oder je Produkt? Je Produkt lohnt sich, wenn die Break-even-Werte deutlich auseinanderliegen.
   5. Welches Tagesbudget soll ein aktives Adset mindestens haben?
   6. Ist Meta euer Hauptmaßstab, und welche Attribution nutzt ihr (z. B. 7 Tage Klick, 1 Tag View)?
   7. Nur mit Triple Whale: Shop-Domain, Attributionsmodell und Fenster (Standard: Triple Attribution, lifetime).
   8. Was wollt ihr mit euren Meta-Ads erreichen? Was soll mit Adsets passieren, die gut laufen, und mit denen, die es nicht tun? In eigenen Worten; auf Wunsch das Beispiel aus [mandat.md](mandat.md) zeigen.
   9. Gibt es Grenzen, die ich nie überschreiten darf (z. B. ein Gesamtbudget pro Tag)? Sonst „keine“.
   10. An welchem Tag hast du den Meta-Token erstellt (für die Erinnerung nach 6 Monaten)?
5. **Mandat festhalten** nach [mandat.md](mandat.md): das Ziel aus Frage 8 im Wortlaut, bei Bedarf mit zwei oder drei kurzen Fragen nachschärfen; Grenzen aus Frage 5 und 9 als Leitplanken. Nennt der Entscheider feste Regeln („ab ROAS X erhöhe ich um Y %“), nachfragen, ob das eine harte Grenze ist (dann Leitplanke) oder dem Urteil des Skills überlassen werden kann. Nicht überspringen: Ohne Ziel meldet `einrichtung.py` die Einrichtung nicht als fertig.
6. **Zusammenfassung** als kurze Tabelle (Stammdaten und Mandat), dann: „Stimmt das so? Antworte mit Ja oder nenne Korrekturen.“ Ohne ausdrückliches Ja nichts schreiben.
7. **Schreiben** nach dem Ja:
   - Ordner `startup/` nach dem Startup umbenennen (Kleinbuchstaben, z. B. `acme`), bei Bedarf mit `git mv`.
   - `startup.json` nach der Feldtabelle unten (auch `meta_token.erstellt`), zuletzt `"beispiel": false`.
   - Profil `README.md`: Name, Einrichtungsdatum, Konten mit Kampagnen, Daten und Attribution, Zielwerte mit Quelle („Einrichtung am <Datum>, <Name>“), Befugnisse.
   - Mandat mit Quelle nach [mandat.md](mandat.md), Schritt 5.
   - Testdaten an die Kontoschlüssel anpassen (Format unten; Werte bleiben erfunden).
   - `docs/TODO.md` abhaken, `docs/CHANGELOG.md` (Einrichtung mit Datum und Person), `AKTUELL.md` („Letzte Sitzungen“ eine Zeile).
8. `einrichtung.py` und Tests erneut. Erwartet: „Stand: alles bereit“.
9. Anbieten: „Sollen wir gleich den ersten echten Lauf machen?“ Wenn ja: `SKILL.md` ab Schritt 1.
10. **Sichern** nach `ANLEITUNG.md` B4: anbieten „Soll ich einen Pull Request erstellen?“, ihn erstellen, den Link nennen und durch das Mergen in GitHub führen. Erklären, warum: Ohne Merge fehlen Einrichtung, Akten und Bericht im nächsten Chat.

## Meta-Token erneuern

Meldet jemand einen erneuerten Token (`ANLEITUNG.md`, B6) oder zeigt die Übersicht die Erinnerung: `einrichtung.py` ausführen. Ist der Meta-Zugang OK, nach Rückfrage `meta_token.erstellt` in `startup.json` auf das Datum des neuen Tokens setzen und sichern (B4). Schlägt der Zugang fehl: B3 prüfen (neuer Wert eingetragen, Republish, neuer Chat).

## Felder in `startup.json`

| Feld | Inhalt |
|---|---|
| `name`, `entscheider`, `systemverantwortlich` | Name des Startups und die beiden Rollen (Namen stehen nur hier) |
| `zeitzone`, `waehrung`, `waehrungszeichen` | wie in den Meta-Konten, z. B. `Europe/Berlin`, `EUR`, `€` |
| `mindestbudget`, `mindestbudget_regel` | Untergrenze aktiver Adsets und die ID der Leitplanke dazu (ohne Leitplanke: `OFFEN`) |
| `zielwerte` | `break_even` je Produkt; `ziel_roas` als eine Zahl für alle Produkte oder je Produkt mit denselben Produktnamen wie `break_even`; `null` = OFFEN |
| `konten` | je Konto: Schlüssel (Kurzname), `id` ohne `act_`, `label`, `meta_name`, eindeutiger `prefix` |
| `meta_token` | `erstellt` (Datum, nie der Token) und `erneuern_nach_tagen` (180); der Skill erinnert 14 Tage vorher |
| `separat` | Kampagnen oder Adsets ohne Verkaufsziel (z. B. Follower); sie bleiben aus Plan und Mindestbudget-Prüfung |
| `triple_whale` | `aktiv: false`, wenn kein Triple Whale genutzt wird; sonst Shop-Domain, Modell, Fenster |

## Testdaten

`<startup>/testdaten/testdaten.json` braucht für jeden Kontoschlüssel aus `startup.json` einen Eintrag, sonst bricht der Testlauf ab. Format je Adset: `tage` = `[Spend, Käufe, Umsatz, Link-Klicks]`, `tw` = `[Käufe, Umsatz, Spend]`, ältester Tag zuerst, letzter Eintrag = gestern. Nur erfundene Werte; bei mehreren Konten die Beispiel-Adsets mit neuen IDs kopieren.

## Erster echter Lauf

Ohne Akten, Learnings und Historie entscheidet der Skill nach Mandat und Fachwissen, nennt die dünne Datenlage offen und lernt aus den Korrekturen des Entscheiders. Akten entstehen automatisch: `build_dataset.py` trägt für jedes aktive Adset die Änderungen der letzten 14 Tage aus Meta ein; danach kommen Vorschläge, Entscheidungen und Gründe hinzu.

## Nie

- Zugangsdaten erfragen, ausgeben oder speichern; `META_WRITE_ENABLED` setzen.
- Werte oder Zielwerte erfinden oder schätzen; Ziel oder Leitplanken ohne ausdrückliche Bestätigung eintragen; von sich aus Regeln oder Schwellen vorschlagen; `"beispiel": false` vor dem Ja des Entscheiders.
- Werbekonten ändern, auch nicht während der Einrichtung.
