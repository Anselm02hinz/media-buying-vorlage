# TODO

Erledigtes abhaken und mit Datum in [CHANGELOG.md](CHANGELOG.md) vermerken.

## Einrichtung (siehe `ANLEITUNG.md`; Stand prüft `einrichtung.py`)

- [ ] `startup.json` mit dem Entscheider ausfüllen, danach `"beispiel": false`.
- [ ] Profil `README.md`: Konten, Kampagnen, Attribution, Zielwerte mit Quellen, Befugnisse.
- [ ] **Media-Buying-Regeln festlegen** (ohne Regeln keine Entscheidungsgrundlage): Startregeln nach `references/regelvorlagen.md` des Skills, vom Entscheider bestätigt, in `regeln/MEDIA_BUYING_REGELN.md` mit Quelle in `docs/quellen/`.
- [ ] Meta-Token (nur `ads_read`, nur die Konten aus `startup.json`) und ggf. Triple-Whale-Key als Umgebungsvariablen der Codex-Umgebung (lokal: `.env`).
- [ ] Testdaten in `testdaten/testdaten.json` an die Kontoschlüssel anpassen.
- [ ] `einrichtung.py` meldet „alles bereit“.

## Beim ersten Lauf

- [ ] Tests ausführen: `python -m unittest discover .agents/skills/media-buying/tests`.
- [ ] Meta-Werte eines Adsets mit dem Ads Manager vergleichen (Spend, Käufe, ROAS, Link-CPC für gestern).
- [ ] Triple-Whale-Abfrage, Modell und Fenster bestätigen (falls aktiv).

## Vorschläge für den Kern

Ideen aus der Arbeit, die den Skill selbst betreffen. Umsetzung nur auf Anweisung des Entscheiders oder des Systemverantwortlichen (siehe `AGENTS.md`).
