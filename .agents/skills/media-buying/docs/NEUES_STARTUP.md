# Neues Startup einrichten

Jedes Startup bekommt ein eigenes Repository: den **Kern** (für alle gleich) und einen eigenen Ordner **`<startup>/`**. Einrichten kann der Systemverantwortliche; Konten, Zielwerte und Regeln bestätigt der Entscheider. Was unbekannt ist, bleibt `null` bzw. OFFEN; nichts schätzen.

## 1. Repository anlegen

Neues privates Repository. Aus einem bestehenden Startup-Repository nur den Kern übernehmen:

`.agents/` (Skill mit Skripten, Tests, Vorlage und Kern-Doku), `AGENTS.md`, `CLAUDE.md`, `README.md`, `.env.example`, `.gitignore`

Nie den Ordner `<startup>/` oder die `.env` eines anderen Startups mitnehmen.

## 2. Startup-Ordner aus der Vorlage

`.agents/skills/media-buying/assets/vorlage_startup/` in den Repository-Root kopieren; die Vorlage selbst bleibt unverändert. Den Ordner nach dem Startup benennen (Kleinbuchstaben, z. B. `acme`) oder `startup` nennen. Die Skripte finden ihn an seiner `startup.json`; im Root darf es nur einen solchen Ordner geben. In dieser Anleitung heißt er `<startup>/`. Kommt das Repository aus der neutralen Vorlage, liegt dort schon `startup/` mit Beispielwerten: diesen Ordner umbenennen statt kopieren.

- Mac/Linux: `cp -R .agents/skills/media-buying/assets/vorlage_startup acme`
- Windows (PowerShell): `Copy-Item .agents/skills/media-buying/assets/vorlage_startup acme -Recurse`

## 3. Probelauf mit Beispielwerten

Solange `<startup>/startup.json` `"beispiel": true` enthält, sind nur Testläufe möglich.

- Tests: `python -m unittest discover .agents/skills/media-buying/tests` (Windows siehe `CLAUDE.md`).
- Testlauf: in `.env` `MEDIA_BUYING_MODUS=test` setzen und „Mach mein Media Buying für heute“ sagen. Ergebnisse landen in `<startup>/testdaten/testlaeufe/`.

## 4. Stammdaten in `<startup>/startup.json`

| Feld | Inhalt |
|---|---|
| `name`, `entscheider`, `systemverantwortlich` | Name des Startups und die beiden Rollen (Namen stehen nur hier) |
| `zeitzone`, `waehrung`, `waehrungszeichen` | wie in den Meta-Konten, z. B. `Europe/Berlin`, `EUR`, `€` |
| `mindestbudget`, `mindestbudget_regel` | Untergrenze aktiver Adsets und die Regel-ID dazu, vom Entscheider bestätigt |
| `zielwerte` | `ziel_roas` und `break_even` je Produkt; `null` = OFFEN |
| `konten` | je Konto: Schlüssel (Kurzname), `id` ohne `act_`, `label`, `meta_name`, eindeutiger `prefix` |
| `separat` | Kampagnen oder Adsets ohne Verkaufsziel (z. B. Follower); sie bleiben aus Plan und Mindestbudget-Prüfung |
| `triple_whale` | `aktiv: false`, wenn kein Triple Whale genutzt wird; sonst Shop-Domain, Modell, Fenster |

Erst wenn alle Werte bestätigt sind: `"beispiel": false`.

## 5. Profil und Regeln

- `<startup>/README.md` (Profil): Name, Einrichtungsdatum, Konten mit Kampagnen, Daten und Attribution, Zielwerte mit Quelle, Befugnisse, startup-spezifische Abweichungen von `AGENTS.md`.
- `<startup>/regeln/MEDIA_BUYING_REGELN.md`: nur Regeln, die der Entscheider vorgibt, mit Quelle in `<startup>/docs/quellen/`. Ohne Regeln schlägt der Skill im Zweifel „Halten“ vor und fragt nach.
- `<startup>/regeln/PRUEFREIHENFOLGE.md`: übernehmen oder mit dem Entscheider anpassen.

## 6. Zugänge

`.env.example` nach `.env` kopieren (nicht versioniert) oder dieselben Namen als Umgebungsvariablen setzen: Meta-Token nur mit `ads_read` und nur für die Konten aus `startup.json`, Triple-Whale-Key nur bei `aktiv: true`. `META_WRITE_ENABLED=0` lassen. Für echte Läufe `MEDIA_BUYING_MODUS` leer lassen.

## 7. Testdaten anpassen

`<startup>/testdaten/testdaten.json` braucht für jeden Kontoschlüssel aus `startup.json` einen Eintrag, sonst bricht der Testlauf ab. Format je Adset: `tage` = `[Spend, Käufe, Umsatz, Link-Klicks]`, `tw` = `[Käufe, Umsatz, Spend]`, ältester Tag zuerst, letzter Eintrag = gestern. Nur erfundene Werte.

## 8. Erster echter Lauf

Der Entscheider startet den Skill. Ohne Akten, Learnings und Historie zeigt der Skill alle Zahlen, nennt fehlende Grundlagen OFFEN und fragt nach Entscheidung und Begründung. Akten entstehen mit dem ersten Lauf: `build_dataset.py` trägt die Änderungen der letzten 14 Tage aus Meta ein, danach kommen Vorschläge, Entscheidungen und Gründe hinzu. Einrichtung mit Datum in `<startup>/docs/CHANGELOG.md` festhalten.

## Kern aktuell halten

Änderungen am Kern stehen in `.agents/skills/media-buying/docs/CHANGELOG.md`. Beim Übertragen in ein anderes Startup-Repository nur Kerndateien ersetzen (den Ordner `.agents/skills/media-buying/` und die Einstiegsdateien im Root), nie `<startup>/`.
