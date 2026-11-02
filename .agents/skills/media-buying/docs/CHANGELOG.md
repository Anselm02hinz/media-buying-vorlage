# Changelog · Kern

Änderungen am Kern (Skill, Skripte, Tests, Arbeitsanweisung, Vorlage), neueste oben. Änderungen eines Startups stehen in dessen `<startup>/docs/CHANGELOG.md`. Dieses Repository ist die neutrale Vorlage: Kernänderungen zuerst hier eintragen und dann in die Startup-Repositorys übertragen (Skill-Ordner und Einstiegsdateien im Root ersetzen, nie den Startup-Ordner).

## 1.0 · 2026-11-02 · Erste neutrale Fassung

Abgeleitet aus dem ersten Pilot-Repository (Kernstand vom 02.11.2026), ohne dessen Startup-Ordner und ohne Git-Historie, damit keine Daten des Pilot-Startups enthalten sind. Auftrag Anselm Hinz (Systemverantwortlicher).

- **Ablauf** (`SKILL.md`): Budgetrunde für die Meta-Konten eines Startups. Daten per API (Meta, optional Triple Whale), Übersicht als Arbeitsgrundlage, Vorschläge je Adset nach den Regeln des Startups und bestätigten Learnings, HTML-Bericht, Ausführungsplan, Freigabe durch den Entscheider, Umsetzung von Hand oder per API (nur mit `META_WRITE_ENABLED=1`), Prüfung.
- **Gedächtnis:** Akte je Adset (`akten/`), Plan je Runde (`runden/YYYY-MM-DD/`), `AKTUELL.md` als Einstieg, `LEARNINGS.md` (Bestätigt / Kandidaten / Überholt; Learnings wirken nur im Spielraum der Regeln und nur bestätigt).
- **Startup-Ordner** `<startup>/`: der einzige Ordner im Repository-Root mit einer `startup.json`, frei benennbar; hier als Beispiel `startup/` mit Beispielwerten (`"beispiel": true`, nur Testläufe möglich).
- **Meta-Abruf:** Änderungsverlauf am Stück und tageweise zusammengeführt, fehlende Budget- und Statuswechsel aus dem letzten eigenen Datenstand abgeleitet; Kontofehler werden Lücke statt Gesamtabbruch. Hinweise zu Metas Aufrufgrenzen in `references/meta-api.md`.
- **Einrichtung:** `docs/NEUES_STARTUP.md`. Tests ohne Netzwerk: `python -m unittest discover .agents/skills/media-buying/tests`.
