# Changelog · Kern

Änderungen am Kern (Skill, Skripte, Tests, Arbeitsanweisung, Vorlage), neueste oben. Änderungen eines Startups stehen in dessen `<startup>/docs/CHANGELOG.md`. Dieses Repository ist die neutrale Vorlage: Kernänderungen zuerst hier eintragen und dann in die Startup-Repositorys übertragen (Skill-Ordner und Einstiegsdateien im Root ersetzen, nie den Startup-Ordner).

## 2.1 · 2026-11-04 · Sicherheitsnetz: Voraussetzungen erkennen

Auftrag: Anselm Hinz (Plan „von 0 auf 1“, Baustein 1). Grund: Ohne gemessene Käufe stand der ROAS auf 0,00, und der Skill hätte nach F-08 alles pausiert. Konten nur mit Kampagnenbudgets oder ganz ohne Kampagnen meldeten trotzdem „alles bereit“, und ohne Werbekonto endete die Einrichtung in einer Schleife zurück zum Token.

- **`scripts/einrichtung.py`:**
  - neue Schritte „Werbekonto“ (Token sieht keins: anlegen oder zuweisen), „Kampagnen“ (Budgetebene der aktiven Adsets, `budgetebenen`) und „Kaufmessung“ (Käufe in 28 Tagen, Pixel `last_fired_time`, `kaufmessung`)
  - Kontostatus „deaktiviert“, „Zahlung offen“ und „geschlossen“ als FEHLT, fast erreichtes Ausgabenlimit als Hinweis
  - `--kampagnen` zeigt die Budgetebene je Kampagne
- **`scripts/build_dataset.py`:**
  - Kontozustand in der Übersicht (`kontozustand`)
  - Konto mit Spend, aber ohne einen gemessenen Kauf (`ohne_kaeufe`): Lücke, ROAS `None` („–“) und Hinweis je Adset
  - eingeschaltete Adsets ohne Auslieferung (`lieferproblem`) in einem eigenen Abschnitt
  - `budget_of` zählt nur Budgets über 0
- **`scripts/common.py`:** `KONTOSTATUS`, `KONTO_GESTOPPT`, `LIEFERPROBLEME` gemeinsam für beide Skripte.
- **Doku:** `SKILL.md` und `references/fachwissen.md` F-15 (bei unklarer Messung nichts kürzen oder pausieren), `references/einrichtung.md` (Chat 2, Schritte 1–3), `references/meta-api.md` (neue Abrufe bei der Einrichtung, UNGEPRÜFT), `ANLEITUNG.md` Teil D. Tests ergänzt.
- **Übertragen in Startup-Repositorys:** Skill-Ordner und `ANLEITUNG.md` ersetzen; im Startup-Ordner nichts nötig.

## 2.0 · 2026-11-04 · Mandat und Fachwissen statt Startregeln

Auftrag: Anselm Hinz. Grund: Starre Startregeln („ab ROAS X um 20 % erhöhen“), die sich ein Startup bei der Einrichtung ausdenkt, sind meist willkürlich. Der Skill soll wie ein Media-Buying-Dienstleister arbeiten: Das Startup nennt sein Ziel, der Skill entscheidet je Runde mit Fachwissen und allen Daten, der Entscheider gibt frei oder korrigiert.

- **Mandat** (`<startup>/regeln/MANDAT.md`, ersetzt `MEDIA_BUYING_REGELN.md`): Ziel im Wortlaut des Entscheiders, Maßstab, optionale Leitplanken (harte Grenzen, IDs `MB-NNNN` wie bisher). Einrichtung nach `references/mandat.md` (ersetzt `references/regelvorlagen.md`); keine Regelvorlagen mehr. `REGELVORSCHLAEGE.md` entfällt: Die KI leitet keine Regeln ab.
- **Fachwissen** (`references/fachwissen.md`, neu): Grundsätze für Datenlage, Lernphase, Budgetschritte, Skalieren, Senken, Abschalten, Wirtschaftlichkeit und Störungen, mit Quellen und Einordnung (offiziell Meta, Branchenpraxis, Faustwert). Liest der Skill in jeder Runde vollständig; IDs `F-NN` in den Grundlagen der Vorschläge.
- **Entscheiden** (`AGENTS.md`, `SKILL.md`, `PRUEFREIHENFOLGE.md`): Rangfolge Leitplanken → Mandat → bestätigte Learnings → Fachwissen. Kein „im Zweifel halten“ mehr; auch Halten braucht einen fachlichen Grund. Der Modus GEMEINSAM_LERNEN (erst fragen) wird ersetzt durch „vorschlagen wie ein Dienstleister, aus Korrekturen lernen“.
- **Learnings** (`references/dokumentation.md`): halten fest, wo der Entscheider anders gewichtet als das Fachwissen; bestätigte Learnings gehen dem Fachwissen vor, nie dem Mandat. Verbindlich wird ein Learning als Leitplanke.
- **`scripts/einrichtung.py`:** prüft `pruefe_mandat` (Ziel nötig, Leitplanken freiwillig, Hinweis auf eine alte `MEDIA_BUYING_REGELN.md`) statt mindestens einer Regel; Kerndateien `references/mandat.md` und `references/fachwissen.md`.
- **`scripts/render_report.py`:** `regeln` je Entscheidung heißt jetzt Grundlagen (`["Mandat v1", "F-04", "L-03"]`); Feld und Format unverändert.
- **Doku und Vorlage:** `ANLEITUNG.md`, `README.md`, `references/einrichtung.md` (Fragen 8–10), `startup/` (Mandat, Prüfreihenfolge, Learnings, AKTUELL, Profil, TODO, Änderungsverlauf, Hinweise in `startup.json`). Tests angepasst.
- **Übertragen in Startup-Repositorys:** Skill-Ordner und Einstiegsdateien im Root ersetzen. Im Startup-Ordner bleibt `regeln/MEDIA_BUYING_REGELN.md` vorerst gültig (als Leitplanken); in der nächsten Sitzung mit dem Entscheider das Mandat festlegen (`references/mandat.md`, „Bestehende Startups mit Regeln“), `REGELVORSCHLAEGE.md` dabei auflösen. `einrichtung.py` meldet bis dahin „Noch kein Ziel im Mandat“.

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
