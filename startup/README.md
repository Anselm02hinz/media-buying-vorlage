# Profil · Beispiel-Startup

Basis-Infos zu diesem Startup an einer Stelle. Eingerichtet nach `ANLEITUNG.md` am OFFEN. Stand OFFEN. OFFEN heißt unbekannt, nicht null und nicht freigegeben. Änderungen nur nach Bestätigung des Entscheiders (`AGENTS.md`).

Werte, die die Skripte nutzen (Entscheider, Konten, Währung, Zeitzone, Zielwerte, Mindestbudget, Triple-Whale-Einstellungen), stehen nur in [startup.json](startup.json). Dieses Profil erklärt Hintergrund, Geltung und Quellen. Aufbau des Ordners: `references/dokumentation.md` des Skills.

## Konten

| Kurzname | Meta-Kontoname | Konto-ID | Währung / Zeitzone | Verkaufskampagnen |
|---|---|---|---|---|
| OFFEN | OFFEN | OFFEN | OFFEN | OFFEN |

Nur diese Konten gehören zum Auftrag; andere Konten nicht abfragen oder bearbeiten. Keine Verkaufs-Adsets (z. B. Follower, Sonstiges), im Bericht separat: OFFEN.

## Daten und Attribution

| Quelle | Festlegung | Beleg |
|---|---|---|
| Meta | Hauptmaßstab? Attributionsfenster, Kaufereignis: OFFEN | |
| Triple Whale | Gegencheck ja/nein, Modell, Fenster, Währung: OFFEN | |
| Zugang | Meta Marketing API (und ggf. Triple-Whale-API); Zugangsdaten nur über Umgebungsvariablen/.env | |

## Zielwerte

| Größe | Wert in `startup.json` | Geltung / Quelle |
|---|---|---|
| Break-even-ROAS je Produkt | `zielwerte.break_even` | OFFEN |
| Ziel-ROAS (für alle Produkte oder je Produkt) | `zielwerte.ziel_roas` | OFFEN |
| Mindestbudget aktiver Adsets | `mindestbudget`, darunter pausieren | OFFEN |
| Weitere harte Grenzen (z. B. Gesamtbudget) | nur als Leitplanke in `regeln/MANDAT.md` | keine eigenen Werte setzen |

Break-even und Ziel-ROAS nicht gleichsetzen. Ziel, Maßstab und Leitplanken stehen im [Mandat](regeln/MANDAT.md).

## Befugnisse

- **Entscheider** und **Systemverantwortlicher**: Namen in `startup.json`. Der Entscheider gibt Budgetpläne frei, legt das Mandat fest und setzt freigegebene Pläne um, solange der Schreibzugriff gesperrt ist; sein Name wird bei `plan.py freigeben --von` eingetragen.
- Der Skill schlägt wie ein Media-Buying-Dienstleister selbst vor (Mandat und Fachwissen); Kontoänderungen nur nach ausdrücklicher Freigabe eines konkreten Plans durch den Entscheider.
- Schreibzugriff per API: **gesperrt** (Token nur `ads_read`, `META_WRITE_ENABLED` nicht gesetzt). Freigegebene Pläne setzt der Entscheider im Ads Manager um. Die KI ändert nie über Browser oder andere Wege.
- Eine spätere dauerhafte Delegation hier festhalten mit: Konten und erlaubten Aktionen, Budget-/Zeitgrenzen, gültiger Mandatsversion, Beginn/Ende, Quelle.

## Ergänzungen und Abweichungen zur Arbeitsanweisung

Diese Punkte gehen `AGENTS.md` vor (Verlauf in [docs/CHANGELOG.md](docs/CHANGELOG.md)). Bisher keine.
