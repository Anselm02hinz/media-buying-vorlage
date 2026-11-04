# Regelvorlagen für die Einrichtung

**Ohne eigene Media-Buying-Regeln hat der Skill keine Entscheidungsgrundlage.** Er zeigt dann nur Zahlen und schlägt im Zweifel „Halten“ vor. Deshalb legt jedes Startup bei der Einrichtung Startregeln fest: Die KI schlägt sie nach dieser Datei vor, der Entscheider bestätigt, passt an oder lehnt ab.

**Das sind Vorschläge, keine Regeln.** Regel wird nur, was der Entscheider ausdrücklich bestätigt oder in eigenen Worten festlegt (`AGENTS.md`, „Regelpflege“). Die Werte unten sind Ausgangspunkte fürs Gespräch, keine Empfehlung für jedes Startup.

## Vorgehen

1. **Zuerst die Zielwerte** aus dem Fragenblock (`references/einrichtung.md`): Break-even je Produkt, Ziel-ROAS (für alle Produkte oder je Produkt), Mindestbudget, Maßstab (Meta oder Triple Whale). Die Vorschläge setzen diese Werte ein. Fehlt ein Wert, steht im Vorschlag OFFEN statt einer Zahl. Gibt es Zielwerte je Produkt, die Regel allgemein fassen („über dem Ziel-ROAS seines Produkts“) und die Werte je Produkt im Vorschlag nennen; die Werte selbst stehen nur in `startup.json`.
2. **Eigene Regeln zuerst:** Hat der Entscheider schon Regeln genannt, diese wörtlich übernehmen und nur die fehlenden Themen mit Vorlagen ergänzen.
3. **Vorschlagen:** höchstens drei bis vier Vorlagen pro Nachricht, je Regel ein Satz in einfachen Worten mit den eingesetzten Werten und die Frage dazu. Beispiel: „Vorschlag: Wenn ein Adset 3 und 7 Tage über eurem Ziel-ROAS von 2,0 liegt und mindestens 5 Käufe hat, erhöhe ich um bis zu 20 %. Passt das, oder wie machst du es?“
4. **Antworten wörtlich festhalten.** Bestätigt: Regel. Angepasst: Regel in der Fassung des Entscheiders. Abgelehnt: weglassen. „Weiß nicht“: weglassen oder mit OFFEN-Stelle, wenn der Entscheider das will.
5. **Pflicht sind mindestens** Datenbasis (R1), Erhöhen (R2), Senken (R4), Pausieren (R5) und Mindestbudget (R7). Fehlt eine davon, nachfragen; ohne Antwort bleibt die Lücke im Bericht OFFEN.
6. **Schreiben** (erst nach dem Ja zur Zusammenfassung):
   - Quelle `<startup>/docs/quellen/Q-YYYYMMDD-001.md`: Datum, Name des Entscheiders, je Regel der Vorschlag und seine Antwort wörtlich.
   - `<startup>/regeln/MEDIA_BUYING_REGELN.md`: Register und je Regel ein Abschnitt im dortigen Format (`## MB-0001 · v1 · <Titel>`, Wenn/Dann, Quelle, Geltungsbereich, offene Begriffe), Regelwerkstand auf 1, gültig ab heute.
   - `startup.json`: `mindestbudget` und `mindestbudget_regel` (ID der Regel zu R7).
   - `<startup>/docs/regelhistorie/AENDERUNGSVERLAUF.md`: ein Eintrag „Startregeln festgelegt“.
7. **Später ändern:** Will der Entscheider eine Regel ändern, gilt die Regelpflege aus `AGENTS.md` (alte Fassung in `docs/regelhistorie/` sichern, neue Version, Quelle).

## Vorlagen

| Nr. | Thema | Vorschlag (Wenn … dann …) | Frage an den Entscheider |
|---|---|---|---|
| R1 | Datenbasis | Nach einer Budget- oder Statusänderung **3 volle Tage** warten, bevor erneut geändert wird; nie allein nach einem Tageswert entscheiden. Ausnahme: klare Störung (z. B. kein Spend trotz aktivem Adset). | Wie viele volle Tage wartest du nach einer Änderung, bevor du wieder änderst? |
| R2 | Erhöhen | Wenn der ROAS über 3 **und** 7 Tage über dem Ziel-ROAS liegt und in 7 Tagen mindestens **5 Käufe** erreicht sind, dann um bis zu **20 %** erhöhen. | Ab wann erhöhst du, und um wie viel höchstens auf einmal? |
| R3 | Halten | Liegt der ROAS zwischen Break-even und Ziel-ROAS, dann halten. | Hältst du in diesem Bereich, oder reagierst du schon früher? |
| R4 | Senken | Wenn der ROAS über 3 **und** 7 Tage unter Break-even liegt, dann um **20–30 %** senken, höchstens bis zum Mindestbudget. | Ab wann senkst du, und um wie viel? |
| R5 | Pausieren | Wenn der ROAS über 7 Tage deutlich unter Break-even liegt (z. B. unter **70 % des Break-even**) oder ein Adset **etwa zwei durchschnittliche Bestellwerte** ohne Kauf ausgegeben hat, dann pausieren. | Wann pausierst du ein Adset statt es zu senken? |
| R6 | Neue Tests | Neue Adsets in den ersten **3 vollen Tagen** halten; vorher nur pausieren, wenn sie den Betrag aus R5 ohne Kauf ausgegeben haben. | Wie viel Zeit oder Budget gibst du einem neuen Test, bevor du entscheidest? |
| R7 | Mindestbudget | Aktive Adsets nie unter **<mindestbudget>** pro Tag; eine begründete Kürzung darunter wird zur Pause. | Welches Tagesbudget soll ein aktives Adset mindestens haben? |
| R8 | Maßstab | Entschieden wird nach dem **Meta-ROAS** (Attribution laut Konto); Triple Whale ist Gegencheck, große Abweichungen nennt der Bericht. | Nach welcher Zahl entscheidest du: Meta, Triple Whale oder beides? |
| R9 | Obergrenze (optional) | Das gesamte Tagesbudget eines Kontos steigt pro Runde um höchstens **<X %>**. | Gibt es eine Grenze, wie stark das Gesamtbudget pro Tag steigen darf? |
