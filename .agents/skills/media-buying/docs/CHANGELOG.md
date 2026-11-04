# Changelog · Kern

Änderungen am Kern (Skill, Skripte, Tests, Arbeitsanweisung, Vorlage), neueste oben. Änderungen eines Startups stehen in dessen `<startup>/docs/CHANGELOG.md`. Dieses Repository ist die neutrale Vorlage: Kernänderungen zuerst hier eintragen und dann in die Startup-Repositorys übertragen (Skill-Ordner und Einstiegsdateien im Root ersetzen, nie den Startup-Ordner).

## 1.2 · 2026-11-04 · Erlaubte Domains für Codex und Claude Code

Auftrag: Anselm Hinz. Grund: Die Anleitung nannte die nötigen Domains nur für Codex. In Claude Code im Web sperrt die Standardstufe „Trusted“ Meta und Triple Whale.

- **`ANLEITUNG.md`:** Hinweis in A1 (`graph.facebook.com`, mit Triple Whale `api.triplewhale.com`), neuer Abschnitt B3a für Claude Code (im Web: „Environment variables“, „Network access“ → „Custom“; lokal: `.env`, Domains nur bei eingeschalteter Sandbox), Verweise in B6 und Teil D.
- **`references/einrichtung.md`**, **`CLAUDE.md`**, **`README.md`:** Internetzugang für beide Umgebungen.
- **`scripts/einrichtung.py`:** Die nächsten Schritte für Meta-Zugang, Internetzugang und Triple Whale nennen auch Claude Code (B3a).
- **Übertragen in Startup-Repositorys:** Skill-Ordner und Einstiegsdateien im Root ersetzen.

## 1.1 · 2026-11-04 · Ziel-ROAS je Produkt

Auftrag: Anselm Hinz, nach einem Einrichtungstest. Grund: Break-even ließ sich je Produkt festlegen, der Ziel-ROAS nur für alle Produkte. Beide Werte sind Eingaben des Entscheiders in `startup.json`; Meta und Triple Whale liefern ROAS je Adset, nicht je Produkt.

- **`startup.json`:** `zielwerte.ziel_roas` ist eine Zahl für alle Produkte (wie bisher) oder je Produkt mit denselben Namen wie `break_even` (`{"Produkt A": 2.2}`). Bestehende Startups brauchen keine Anpassung.
- **`scripts/einrichtung.py`:** prüft beide Formen (`pruefe_zielwerte`): OFFEN je fehlendem Produktwert, FEHLT bei Platzhaltern und Werten, die keine Zahl sind, HINWEIS bei einem Ziel-ROAS unter dem Break-even eines Produkts.
- **`scripts/render_report.py`:** Der Bericht nennt den Ziel-ROAS je Produkt, wenn er so festgelegt ist (`targets_text`).
- **Doku:** Fragenblock und Feldtabelle (`references/einrichtung.md`), `references/regelvorlagen.md`, `SKILL.md` (je Adset die Zielwerte seines Produkts), `ANLEITUNG.md`, Vorlage `startup/startup.json` (Hinweis) und `startup/README.md` (Zielwerte). Tests ergänzt.
- **Übertragen in Startup-Repositorys:** Skill-Ordner und `ANLEITUNG.md` ersetzen. Für Ziel-ROAS je Produkt `ziel_roas` in `startup.json` nach Bestätigung des Entscheiders umstellen und die Quelle im Profil nennen.

## 1.0 · 2026-11-02 · Erste neutrale Fassung

Erste Fassung der neutralen Vorlage. Auftrag: Systemverantwortlicher.

- **Ablauf** (`SKILL.md`): Budgetrunde für die Meta-Konten eines Startups. Daten per API (Meta, optional Triple Whale), Übersicht als Arbeitsgrundlage, Vorschläge je Adset nach den Regeln des Startups und bestätigten Learnings, HTML-Bericht, Ausführungsplan, Freigabe durch den Entscheider, Umsetzung von Hand oder per API (nur mit `META_WRITE_ENABLED=1`), Prüfung.
- **Gedächtnis:** Akte je Adset (`akten/`), Plan je Runde (`runden/YYYY-MM-DD/`), `AKTUELL.md` als Einstieg, `LEARNINGS.md` (Bestätigt / Kandidaten / Überholt; Learnings wirken nur im Spielraum der Regeln und nur bestätigt).
- **Startup-Ordner** `<startup>/`: der einzige Ordner im Repository-Root mit einer `startup.json`, frei benennbar; hier als Beispiel `startup/` mit Beispielwerten (`"beispiel": true`, nur Testläufe möglich).
- **Meta-Abruf:** Änderungsverlauf am Stück und tageweise zusammengeführt, fehlende Budget- und Statuswechsel aus dem letzten eigenen Datenstand abgeleitet; Kontofehler werden Lücke statt Gesamtabbruch. Hinweise zu Metas Aufrufgrenzen in `references/meta-api.md`.
- **Regeln:** Ohne eigene Media-Buying-Regeln hat der Skill keine Entscheidungsgrundlage. Bei der Einrichtung schlägt die KI Startregeln nach `references/regelvorlagen.md` vor, der Entscheider bestätigt oder passt an; `einrichtung.py` meldet die Einrichtung erst mit Regeln als fertig.
- **Meta-Zugang:** Standard-API-Version `v26.0`, zentral in `scripts/common.py` (überschreibbar mit `META_API_VERSION`). Systemnutzer-Token ohne Ablauf, Erneuerung alle 180 Tage (`startup.json`, `meta_token`); Erinnerung 14 Tage vorher in Übersicht und `einrichtung.py`.
- **Einrichtung:** Versand als ZIP (`README.md`), Schritt-für-Schritt-Anleitung für den Media Buyer in `ANLEITUNG.md` (ZIP → GitHub → Codex), geführte Einrichtung durch die KI nach `references/einrichtung.md`; `scripts/einrichtung.py` prüft nur lesend Upload, Stammdaten, Testdaten, Zugänge, Werbekonten und Kampagnen und nennt den nächsten Schritt. Tests ohne Netzwerk: `python -m unittest discover .agents/skills/media-buying/tests`.
