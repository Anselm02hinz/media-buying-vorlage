# TODO

Erledigtes abhaken und mit Datum in [CHANGELOG.md](CHANGELOG.md) vermerken.

## Einrichtung (siehe `.agents/skills/media-buying/docs/NEUES_STARTUP.md`)

- [ ] `startup.json` mit dem Entscheider ausfüllen, danach `"beispiel": false`.
- [ ] Profil `README.md`: Konten, Kampagnen, Attribution, Zielwerte mit Quellen, Befugnisse.
- [ ] Regeln des Entscheiders in `regeln/MEDIA_BUYING_REGELN.md` (mit Quelle in `docs/quellen/`) oder bewusst leer lassen.
- [ ] Meta-Token (nur `ads_read`, nur die Konten aus `startup.json`) und ggf. Triple-Whale-Key in `.env`.
- [ ] Testdaten in `testdaten/testdaten.json` an die Kontoschlüssel anpassen.

## Beim ersten Lauf

- [ ] Tests ausführen: `python -m unittest discover .agents/skills/media-buying/tests`.
- [ ] Meta-Werte eines Adsets mit dem Ads Manager vergleichen (Spend, Käufe, ROAS, Link-CPC für gestern).
- [ ] Triple-Whale-Abfrage, Modell und Fenster bestätigen (falls aktiv).

## Vorschläge für den Kern

Ideen aus der Arbeit, die den Skill selbst betreffen. Umsetzung nur auf Anweisung des Entscheiders oder des Systemverantwortlichen (siehe `AGENTS.md`).
