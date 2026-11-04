# Mandat festlegen

**Das Mandat ist die Entscheidungsgrundlage des Skills.** Wie ein Startup einem Media-Buying-Dienstleister sagt, was es erreichen will, hält es bei der Einrichtung sein Ziel fest. Wie das Ziel erreicht wird, entscheidet der Skill in jeder Runde nach Fachwissen ([fachwissen.md](fachwissen.md)) und den Daten; jeder Vorschlag braucht die Freigabe des Entscheiders. Starre Regeln („ab ROAS X um 20 % erhöhen“) gehören nicht ins Mandat: Meist sind sie willkürlich und schlechter als ein begründetes Urteil über das einzelne Adset.

## Bestandteile

| Teil | Inhalt | Wo | Pflicht |
|---|---|---|---|
| Ziel | Was das Startup mit den Meta-Ads erreichen will, in den Worten des Entscheiders | `<startup>/regeln/MANDAT.md` | ja |
| Maßstab | Nach welcher Zahl bewertet wird (Meta, Triple Whale oder beides) und welche Attribution | `MANDAT.md` | ja |
| Zielwerte | Break-even je Produkt, Ziel-ROAS für alle oder je Produkt | `startup.json`, `zielwerte` | ja; einzelne Werte dürfen OFFEN sein |
| Leitplanken | Harte Grenzen, die der Skill nie überschreitet | `MANDAT.md` | nein; zum Mindestbudget empfohlen |

## Vorgehen

1. **Ziel erfragen** (Fragenblock in [einrichtung.md](einrichtung.md)): „Was wollt ihr mit euren Meta-Ads erreichen? Was soll mit Adsets passieren, die gut laufen, und mit denen, die es nicht tun?“ Tut sich der Entscheider schwer, dieses Beispiel zeigen und in seinen Worten anpassen lassen:

   > Wir wollen mit allen Adsets den Ziel-ROAS erreichen. Adsets, bei denen das nach ernsthaften Versuchen nicht gelingt, werden heruntergefahren oder abgeschaltet. Adsets, die gut laufen, werden so weit wie möglich gepusht. Das Budget soll bestmöglich eingesetzt werden, um neue Kunden zu gewinnen und den Deckungsbeitrag zu erreichen.

2. **Nachschärfen, nur wo das Ziel offenlässt, was dem Entscheider wichtig ist**, mit höchstens zwei oder drei kurzen Fragen, z. B.: Geht Wachstum oder Profitabilität vor, wenn beides nicht zugleich geht? Gibt es ein Gesamtbudget, das nicht überschritten werden soll? Wie viel darf ein neuer Test kosten, bevor er sich bewähren muss? Antworten gehören ins Ziel oder, wenn es eine harte Grenze ist, in die Leitplanken.
3. **Leitplanken nur auf Wunsch.** Fragen: „Gibt es Grenzen, die ich nie überschreiten darf?“ Empfohlen ist eine Leitplanke zum Mindestbudget (`startup.json`, `mindestbudget`), weil sehr kleine Budgets kaum auswertbare Daten liefern. Keine Leitplanken vorschlagen, die der Entscheider nicht selbst will.
4. **Nicht vorschlagen:** feste Prozentstaffeln, ROAS-Schwellen für bestimmte Zeitfenster, Wartefristen als Regel. Diese Fragen beantwortet der Skill je Runde fachlich und begründet; den Stil des Entscheiders lernt er aus dessen Korrekturen (Learnings).
5. **Schreiben**, erst nach dem Ja zur Zusammenfassung in [einrichtung.md](einrichtung.md):
   - Quelle `<startup>/docs/quellen/Q-YYYYMMDD-001.md`: Datum, Name des Entscheiders, Fragen und Antworten wörtlich.
   - `<startup>/regeln/MANDAT.md`: Ziel im Wortlaut des Entscheiders (sprachlich geglättet nur mit seinem Ja), Maßstab, Leitplanken im dortigen Format (`## MB-0001 · v1 · <Titel>`), Mandat v1, gültig ab heute.
   - `startup.json`: `mindestbudget` und `mindestbudget_regel` (ID der Leitplanke zum Mindestbudget, ohne Leitplanke `OFFEN`).
   - `<startup>/docs/regelhistorie/AENDERUNGSVERLAUF.md`: ein Eintrag „Mandat v1 festgelegt“.
6. **Später ändern:** nach `AGENTS.md`, Abschnitt „Mandat und Leitplanken“ (alte Fassung sichern, neue Version, Quelle).

## Bestehende Startups mit Regeln

Hat ein Startup noch `<startup>/regeln/MEDIA_BUYING_REGELN.md` aus einer früheren Version, gelten dessen Regeln bis zur Umstellung als Leitplanken. Umstellen in einer Sitzung mit dem Entscheider: Ziel erfragen (oben), jede bisherige Regel durchgehen (als Leitplanke behalten oder dem Urteil des Skills überlassen) und alles in `MANDAT.md` übernehmen. Die alte Datei nach `docs/regelhistorie/` verschieben und den Änderungsverlauf ergänzen.
