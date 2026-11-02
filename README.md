# Media Buying · Budgetrunde

Budgetierung von Meta-Werbekonten mit KI: Der Entscheider startet die Budgetrunde in Codex oder Claude Code. Der Skill holt Meta- und Triple-Whale-Daten per API, gleicht sie mit früheren Entscheidungen ab, schlägt Budgets in einem HTML-Bericht vor und setzt nur Freigegebenes um.

Dieses Repository gehört zu: **siehe `<startup>/startup.json`** (Name, Entscheider, Konten) und dem Profil [<startup>/README.md](<startup>/README.md).

## Aufbau

```
AGENTS.md  CLAUDE.md  README.md  .env.example  .gitignore    Einstieg (Kern, im Root nötig)

.agents/skills/media-buying/     KERN – für jedes Startup gleich, als Ganzes übertragbar
├── SKILL.md                     Ablauf der Budgetrunde
├── scripts/                     Abruf, Datenstand, Bericht, Plan
├── references/                  liest die KI gezielt: Meta-API, Triple-Whale-API, Dokumentation und Ablage
├── tests/                       Tests ohne Netzwerk
├── assets/vorlage_startup/      Startpaket für ein neues Startup
└── docs/                        für Menschen: NEUES_STARTUP.md, CHANGELOG.md des Kerns

<startup>/                       STARTUP – alles Individuelle (Ordner mit startup.json, z. B. startup/ oder acme/)
├── startup.json                 Stammdaten für die Skripte
├── README.md                    Profil: Konten, Daten und Attribution, Zielwerte, Befugnisse, Abweichungen
├── AKTUELL.md                   Einstieg jeder Sitzung
├── LEARNINGS.md                 wie der Entscheider entscheidet
├── regeln/                      Regeln, Prüfreihenfolge, Regelvorschläge
├── akten/                       Akte je Adset (Gedächtnis des Skills)
├── runden/YYYY-MM-DD/           alles einer Runde: Datenstand, Übersicht, Bericht, Plan, Verifikation
├── testdaten/                   erfundene Testdaten und Testläufe
└── docs/                        Nachweise und Verlauf: Quellen, Regelhistorie, TODO, CHANGELOG
```

Faustregel: Was der Skill in einer Runde liest oder schreibt, liegt direkt in `<startup>/` oder in `regeln/`, `akten/`, `runden/`; was nur belegt oder den Verlauf festhält, in `docs/`. Einzelheiten: [dokumentation.md](.agents/skills/media-buying/references/dokumentation.md).

## Ablauf einer Budgetrunde

| Schritt | Skript | Ergebnis |
|---|---|---|
| Daten holen | `fetch_meta.py`, `fetch_triple_whale.py` | Rohdaten: Konten, Adsets, Tageswerte, Änderungsverlauf mit Person; TW-Käufe je Adset (nur lokal) |
| Datenstand und Abgleich | `build_dataset.py` | Datenstand, **Übersicht** (Arbeitsgrundlage der KI), jede Meta-Änderung in Akte und Plan eingeordnet („wie entschieden“, „abweichend“, „ohne Plan“), offene Fragen an den Entscheider |
| Entscheiden und Bericht | KI, dann `render_report.py` | HTML-Bericht, Ausführungsplan, Vorschlag je Adset in der Akte |
| Freigabe | `plan.py korrigieren`, `freigeben`, `begruenden` | Entscheidung und Gründe des Entscheiders in Plan und Akte |
| Umsetzen und prüfen | Entscheider im Ads Manager bzw. `plan.py ausfuehren` (nur mit `META_WRITE_ENABLED=1`), `plan.py pruefen` | Verifikation, Prüfergebnis in der Akte |

Einzelheiten: [SKILL.md](.agents/skills/media-buying/SKILL.md). Dokumentation (Plan = Dokumentation der Runde für Menschen, Akte je Adset = Gedächtnis des Skills, `AKTUELL.md` = Einstieg jeder Sitzung): [dokumentation.md](.agents/skills/media-buying/references/dokumentation.md).

## Einrichtung und Tests

- Neues Startup: [NEUES_STARTUP.md](.agents/skills/media-buying/docs/NEUES_STARTUP.md).
- Zugänge: `.env.example` nach `.env` kopieren (wird nicht versioniert) oder dieselben Namen als Umgebungsvariablen setzen. Schreibzugriff auf Meta bleibt aus, bis Entscheider oder Systemverantwortlicher ihn freischalten.
- Testlauf ohne Zugänge: `MEDIA_BUYING_MODUS=test` (erfundene Daten aus `<startup>/testdaten/`, Ergebnisse nur in `<startup>/testdaten/testlaeufe/`).
- Tests: `python -m unittest discover .agents/skills/media-buying/tests` (Python ≥ 3.9, keine Pakete; unter Windows zusätzlich `tzdata`, z. B. `uv run --no-project --with tzdata python -m unittest discover .agents/skills/media-buying/tests`).
- Änderungen am Kern: [CHANGELOG.md](.agents/skills/media-buying/docs/CHANGELOG.md) · Änderungen des Startups: `<startup>/docs/CHANGELOG.md` · offene Punkte: `<startup>/docs/TODO.md`.
