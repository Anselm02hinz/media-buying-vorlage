# Fachwissen · Budgetsteuerung von Meta-Adsets

Grundlage für das fachliche Urteil des Skills, wie es ein erfahrener Media Buyer hat, der ein Meta-Konto als Dienstleister führt. Der Skill liest diese Datei in jeder Runde vollständig. Sie gilt für Verkaufs-Adsets mit eigenem Tagesbudget (ABO) im E-Commerce.

**So anwenden:**
- **Urteil, keine Automatik.** Die Grundsätze erklären, worauf es ankommt; entschieden wird je Adset nach seiner Lage. Faustwerte sind Orientierung. Wer davon abweicht, begründet es.
- **Rangfolge:** Leitplanken im Mandat → Ziel und Zielwerte des Mandats → bestätigte Learnings des Entscheiders → dieses Fachwissen. Hat der Entscheider einen anderen Stil bestätigt (z. B. größere Schritte), gilt sein Stil.
- **Zitieren:** In den Grundlagen eines Vorschlags die tragenden Grundsätze nennen (`F-05`). Faustwerte nie als Regel des Startups ausgeben.
- **Einordnung** je Grundsatz: *offiziell Meta* (Meta-Hilfe oder Entwicklerdoku), *Branchenpraxis*, *Faustwert* (verbreitet, nicht belegt), *Ableitung* (aus den übrigen Grundsätzen geschlossen).

Stand der Quellen: 04.11.2026. Meta ändert Oberflächen und Regeln häufig; beim Aktualisieren die Quellen neu prüfen.

## Denkweise

1. **Das Budget gehört dorthin, wo der nächste Euro am meisten bringt**, gemessen am Ziel des Mandats (Ziel-ROAS, Deckungsbeitrag, Neukunden).
2. **Signal von Rauschen trennen.** Wenige Käufe und einzelne Tage täuschen; entschieden wird auf belastbaren Zahlen.
3. **Wenige, begründete Änderungen** statt täglichem Drehen. Jede Änderung stört die Auslieferung ein wenig und macht die nächste Bewertung unschärfer.
4. **Konsequent in beide Richtungen.** Gewinner ausbauen, solange sie tragen; Verlierer nach einem fairen Versuch zurückfahren oder abschalten. Halten ist eine bewusste Entscheidung, keine Ausrede.
5. **Ursache richtig zuordnen.** Budget löst keine Creative-, Tracking- oder Kontoprobleme.

## Grundsätze

### F-01 · Datenlage und Rauschen

**Grundsatz:** Meta empfiehlt, die Leistung über mindestens eine volle Woche zu bewerten; Tages- und Stundenwerte schwanken und gleichen sich aus. Kaufzahlen sind zufällig verteilt (Poisson). Bei wenigen Käufen ist der wahre Wert sehr unsicher, der ROAS streut wegen schwankender Warenkörbe zusätzlich:

| Beobachtete Käufe | Wahrer Wert liegt mit 95 % zwischen |
|---|---|
| 5 | dem 0,32- und 2,33-Fachen |
| 10 | dem 0,48- und 1,84-Fachen |
| 20 | dem 0,61- und 1,54-Fachen |
| 50 | dem 0,74- und 1,32-Fachen |

**Anwendung:** Nie allein wegen eines Tages eingreifen. Grundlage sind 7 Tage und die Phase seit der letzten Änderung, immer mit der Kaufzahl dazu. Unter etwa 10 Käufen nur grobe Aussagen: deutliche Abweichungen zählen, knappe nicht. Gestern und 3 Tage zeigen die Richtung, nicht das Urteil.

*Offiziell Meta (Zeitraum); Intervalle eigene Rechnung · [Meta: Kosten pro Ergebnis](https://www.facebook.com/business/help/1364841787225722)*

### F-02 · Meldeverzug und Zuordnung

**Grundsatz:** Käufe außerhalb von Meta (Web-Käufe) ordnet Meta seit dem 10.06.2025 dem Tag des Kaufs zu, Klicks dem Tag der Impression. Insights werden laufend aktualisiert und ändern sich nach 28 Tagen nicht mehr. Mit 7-Tage-Klick-Attribution kommen Käufe aus früheren Klicks noch Tage später herein. Seit dem 12.01.2026 liefert die API keine Daten mehr für die Fenster 7d_view und 28d_view.

**Anwendung:** „Gestern“ ist vorläufig und fällt eher zu niedrig aus. Die ersten Tage nach einer Änderung enthalten noch Käufe aus Klicks davor; eine Wirkungskontrolle braucht deshalb Abstand zur Änderung (*Ableitung*). Den Tag der Änderung selbst nicht als Vergleichstag werten. Daten vor und nach Juni 2025 nicht direkt vergleichen.

*Offiziell Meta · [Insights Best Practices](https://developers.facebook.com/documentation/ads-commerce/marketing-api/insights/best-practices.md), [Änderungen 2025](https://developers.facebook.com/documentation/ads-commerce/marketing-api/out-of-cycle-changes/occ-2025.md), [Attribution](https://www.facebook.com/business/help/460276478298895)*

### F-03 · Lernphase

**Grundsatz:** Ein Adset verlässt die Lernphase meist nach etwa 50 Ergebnissen in der Woche nach der letzten signifikanten Änderung. In der Lernphase ist die Leistung weniger stabil und der CPA meist höher; die Werte sagen nicht unbedingt etwas über die spätere Leistung. „Learning limited“ heißt: voraussichtlich keine 50 Ergebnisse pro Woche, etwa wegen zu kleinem Budget, kleinem Publikum oder Überschneidung mit anderen Adsets.

**Anwendung:** Schwache Zahlen kurz nach Start oder nach einer großen Änderung nicht als Endurteil werten. Ein dauerhaft lernbegrenztes Adset ist eher zu klein budgetiert oder zu eng als schlecht. Der Lernstatus steht nicht im Datenstand (siehe „Was der Datenstand nicht zeigt“).

*Offiziell Meta · [Lernphase](https://www.facebook.com/business/help/112167992830700), [Learning limited](https://www.facebook.com/business/help/269269737396981)*

### F-04 · Änderungen, Pausen und Reaktivierung

**Grundsatz:** Signifikante Änderungen setzen die Lernphase zurück. Immer signifikant sind Änderungen an Targeting, Creative, Optimierungsereignis oder Gebotsstrategie, eine neue Anzeige und eine **Pause von 7 Tagen oder mehr**. Bei Budgetänderungen hängt es von der Größe ab: Metas Beispiel ist 100 $ → 101 $ eher nicht, 100 $ → 1.000 $ möglicherweise schon. Eine offizielle Prozentgrenze gibt es nicht. Meta rät, das Budget nicht häufig und nur mit Grund zu ändern; häufiges An- und Ausschalten stört die Auslieferung.

**Anwendung:** Lieber selten und deutlich als oft und kleinteilig ändern. Kein Pendeln zwischen An und Aus. Wer ein Adset länger als eine Woche pausiert, startet es später neu und muss mit einer neuen Lernphase rechnen. Ist ein Adset nur vorübergehend schwach, ist Senken oft besser als Pausieren.

*Offiziell Meta · [Signifikante Änderungen](https://www.facebook.com/business/help/316478108955072), [Budget ändern](https://www.facebook.com/business/help/414038972972624), [Anzeigen pausieren](https://www.facebook.com/business/help/204798856225114)*

### F-05 · Schrittgröße und Takt

**Grundsatz:** Üblich sind Budgetschritte von etwa 15–25 %, je nach Quelle 10–30 %, mit einigen Tagen Abstand. Das ist Folklore, keine Meta-Vorgabe: Ads Manager selbst hat in einem dokumentierten Fall eine Erhöhung um 79 % ohne neue Lernphase angeboten.

**Anwendung:** Die Schrittgröße richtet sich nach der Belastbarkeit und dem Abstand zum Ziel. Ein Adset deutlich über dem Ziel mit vielen Käufen verträgt einen größeren Schritt, eines knapp über dem Ziel mit wenigen Käufen einen kleinen. Dasselbe Adset nicht täglich ändern; nach einer Änderung erst die Wirkung sehen (F-02), außer bei einer klaren Störung. Hat der Entscheider einen eigenen Stil bestätigt, gilt dieser.

*Faustwert · [Jon Loomer: Do not touch](https://www.jonloomer.com/do-not-touch-a-facebook-ad-thats-working/), [Jon Loomer: Budget-Updates](https://www.jonloomer.com/updates-to-meta-ads-budgeting/)*

### F-06 · Pacing: Ausgaben weichen vom Tagesbudget ab

**Grundsatz:** Ein Tagesbudget ist ein Wochendurchschnitt (Sonntag bis Samstag). Meta darf an einem Tag bis zu 75 % mehr ausgeben, in der Woche höchstens das Siebenfache des Tagesbudgets; mit Budget-Sharing zwischen Adsets kommen bis zu 20 % hinzu. Am Tag einer Änderung gilt als Obergrenze das 1,75-Fache des höchsten an diesem Tag gültigen Budgets. Ändert man spät am Tag, gibt Meta an diesem Tag zu viel oder zu wenig aus. Die Mehrausgabe von 75 % führt Meta laut einigen Hilfeseiten schrittweise ein, die Entwicklerdoku nennt noch 25 %.

**Anwendung:** Tagesausgaben über oder unter dem Budget sind normal, kein Fehler. Änderungen früh am Tag in der Zeitzone des Kontos umsetzen lassen. Budgetsummen im Bericht sind eingestellte Budgets, keine Ausgabenprognose.

*Offiziell Meta · [Tagesbudget](https://www.facebook.com/business/help/190490051321426), [Mehrausgaben](https://www.facebook.com/business/help/525189242169568), [Budget und Ergebnisse](https://www.facebook.com/business/help/203183363050448)*

### F-07 · Budget im Verhältnis zu den Kosten pro Kauf

**Grundsatz:** Metas eigene Faustregel: Das Tagesbudget sollte mindestens das Zehnfache der durchschnittlichen Kosten pro Optimierungsereignis betragen (mit Kostenziel mindestens das Fünffache des Ziels). Gegen „Learning limited“ empfiehlt Meta, Adsets zusammenzulegen, das Budget zu erhöhen oder das Publikum zu erweitern.

**Anwendung:** Ein Adset weit unter dem Zehnfachen des CPA liefert wenig belastbare Daten und kommt kaum aus der Lernphase. Ein Adset durch Kürzen „auszuhungern“ bringt meist nichts. Muss es weit unter dieses Niveau, ist Pausieren oft ehrlicher (*Ableitung*). Viele kleine Adsets sind schwächer als wenige ausreichend budgetierte.

*Offiziell Meta (von Meta als Faustregel bezeichnet) · [Budget-Empfehlungen](https://www.facebook.com/business/help/164406965378460)*

### F-08 · Fairer Versuch vor Senken oder Abschalten

**Grundsatz:** Bevor ein Adset abgeschaltet wird, braucht es einen fairen Versuch. Verbreitet ist: etwa das Dreifache des Ziel-CPA ausgeben, bevor man entscheidet; die Spanne in der Branche reicht von 1,5× bis 5×. Ohne Kauf nach diesem Betrag abschalten, mit wenigen Käufen eventuell noch einmal etwa 1× Ziel-CPA geben. Früher abschalten ist vertretbar, wenn ein Adset trotz Budget nicht ausliefert oder abgelehnt ist. Meta rät, hohe Kosten erst nach der Lernphase zu bewerten.

**Anwendung:** Ziel-CPA aus den Daten ableiten: durchschnittlicher Warenkorb (Umsatz ÷ Käufe) ÷ Ziel-ROAS des Produkts. Zwei Fälle trennen:
- **Keine oder kaum Käufe** nach einem fairen Versuch: pausieren.
- **Käufe vorhanden, ROAS unter Ziel:** Abstand und Belastbarkeit entscheiden. Klar unter Break-even mit ausreichend Käufen: deutlich senken oder pausieren. Zwischen Break-even und Ziel: halten oder behutsam senken; die Tendenz und das Mandat entscheiden (z. B. Neukundengewinnung).

Ein „ernsthafter Versuch“ im Sinne des Mandats ist ein fairer Versuch in diesem Sinn.

*Faustwert · [Flighted: Wann pausieren](https://www.flighted.co/blog/how-to-know-when-to-pause-a-meta-ad), [Meta: hohe Kosten](https://www.facebook.com/business/help/2727273724224874)*

### F-09 · Skalieren und abnehmender Grenzertrag

**Grundsatz:** Metas System kauft zuerst die günstigsten Gelegenheiten; mit mehr Budget steigen die Kosten pro Ergebnis. Für die Budgetverteilung zählt der Ertrag des nächsten Euros (Grenz-ROAS), nicht der Durchschnitt. Horizontal skalieren (Duplikate) startet neue Lernphasen und erzeugt Überschneidungen, die die Leistung beim Skalieren schwerer vorhersagbar machen.

**Anwendung:** Der Durchschnitts-ROAS überschätzt, was eine Erhöhung bringt. Nach einer Erhöhung den Zusatzertrag prüfen: Mehrumsatz ÷ Mehrspend gegenüber der Phase davor. Hält er das Ziel, weiter erhöhen. Fällt er klar darunter, ist die Grenze erreicht: halten oder einen Schritt zurück. Gewinner bevorzugt vertikal erhöhen; ähnliche Adsets eher zusammenlegen als vervielfachen (das schlägt der Skill dem Entscheider als Hinweis vor, es ist keine Budgetzeile). Wie stark der CPA beim Skalieren typischerweise steigt, ist nicht belegt.

*Offiziell Meta (Mechanik) · [Kosten pro Ergebnis](https://www.facebook.com/business/help/1364841787225722), [Robyn](https://facebookexperimental.github.io/Robyn/docs/features/), [Auktionsüberschneidung](https://www.facebook.com/business/help/537699989762051)*

### F-10 · Breakdown-Effekt

**Grundsatz:** Meta steuert Auslieferung nach dem künftigen Grenzertrag. Durchschnittswerte in Aufschlüsselungen (Platzierung, Uhrzeit, Anzeige) sind deshalb irreführend; scheinbar teure Teile können das Gesamtergebnis verbessern. Bewertet wird auf der Ebene, auf der das Budget liegt.

**Anwendung:** Bei Adset-Budgets sind Vergleiche zwischen Adsets zulässig. Ein Adset nicht wegen schwacher Werte einzelner Anzeigen oder Platzierungen kürzen. Budget-Sharing zwischen Adsets verwischt die Zuordnung etwas.

*Offiziell Meta · [Breakdown-Effekt](https://www.facebook.com/business/help/770303663944673)*

### F-11 · Wirtschaftlichkeit: Break-even, Deckungsbeitrag, Neukunden

**Grundsatz:** Der Deckungsbeitrag ist der Umsatz minus aller variablen Kosten vor Werbung (Wareneinsatz, Versand, Zahlungsgebühren, Retouren). Der Break-even-ROAS ist 1 ÷ Deckungsbeitragsquote; bei 35 % liegt er bei 2,86. Der ROAS auf den Erstkauf ist die vorsichtige Hürde; Folgekäufe rechtfertigen niedrigere Werte nur, wenn das Startup das so vorgibt. Der Meta-ROAS enthält auch Bestandskunden. Triple Whale weist mit NC-ROAS den Umsatz aus Neukunden-Bestellungen je Werbeeuro aus.

**Anwendung:** Break-even und Ziel-ROAS des Produkts aus `startup.json` sind die Messlatte. Über Break-even verdient ein Adset Deckungsbeitrag, über dem Ziel-ROAS erfüllt es das Mandat. Will das Mandat Neukunden, ist ein hoher ROAS mit wenig Neukunden (soweit sichtbar) kein automatischer Grund zu skalieren.

*Branchenpraxis · [eightx: ROAS und Deckungsbeitrag](https://eightx.co/blog/roas-vs-contribution-margin), [Triple Whale: NC-ROAS](https://triplewhale.readme.io/docs/nc-roas), [Jon Loomer: Zielgruppen-Segmente](https://www.jonloomer.com/audience-segments-manual-sales-campaign/)*

### F-12 · Meta und Triple Whale

**Grundsatz:** Meta warnt davor, Ergebnisse verschiedener Attributionsmodelle zu vergleichen. Meta zählt auch Käufe nach Ansicht und ordnet geräteübergreifend zu; Triple Whale hängt an eigenem Pixel und UTM-Parametern und gibt anderen Kanälen Anteile. Abweichungen in beide Richtungen sind normal. Einzelne Anbieter schätzen, dass Plattformen ihre Ergebnisse um 20–40 % überzeichnen; belegt ist das nicht.

**Anwendung:** Nach dem Maßstab des Mandats entscheiden, die andere Quelle als Gegencheck. Quellen nie addieren oder mischen. Aufschlussreich ist das Verhältnis Meta zu TW je Adset: Verschiebt es sich deutlich, ist das ein Signal (Tracking, Zuordnung, Zielgruppe) und gehört in den Bericht.

*Branchenpraxis; Vergleichswarnung offiziell Meta · [Meta: Attribution](https://www.facebook.com/business/help/460276478298895), [Angler: Abweichungen](https://www.getangler.ai/blog/why-triplewhale-and-facebook-attribution-dont-match)*

### F-13 · Budget löst keine Creative-Probleme

**Grundsatz:** Meta meldet „Creative limited“, wenn die Kosten pro Ergebnis über denen früherer Anzeigen liegen, und „Creative fatigue“ ab dem Doppelten. Das Gegenmittel ist ein neues, deutlich anderes Creative oder ein breiteres Publikum, nicht mehr Budget. Bei Optimierung auf Käufe ist der CPM laut Meta kein guter Indikator.

**Anwendung:** Fällt ein bislang gutes Adset über Tage ab und steigt der Link-CPC deutlich, spricht das eher für Ermüdung als für Zufall (*Ableitung*). Dann nicht erhöhen, höchstens senken, um den Schaden zu begrenzen, und dem Entscheider „neues Creative prüfen“ melden. Frequenz-Schwellen wie „über 3“ sind Folklore.

*Offiziell Meta · [Creative fatigue](https://www.facebook.com/business/help/1346816142327858), [Kosten pro Ergebnis](https://www.facebook.com/business/help/1364841787225722)*

### F-14 · Saison, Wochentage und Aktionen

**Grundsatz:** Hochphasen (Black Friday, Weihnachten, eigene Sales) verändern Kosten und Konversionsraten; Branchenbeobachtungen zeigen deutlich höhere Kosten in Hochphasen, belastbare Zahlen gibt es nicht. Meta bietet für erwartete Spitzen eine Budgetplanung (nur Tagesbudgets, bis zum Achtfachen). Wochentage unterscheiden sich, auch wegen der Budgetwoche Sonntag bis Samstag (F-06).

**Anwendung:** Aktionstage im Bericht als Störfaktor nennen. Nicht auf Basis eines Aktions-ROAS skalieren und nicht direkt nach einer Aktion kürzen, weil der Rückgang erwartbar ist. Volle 7-Tage-Fenster oder gleiche Wochentage vergleichen. Bekannte Aktionen stehen idealerweise in `AKTUELL.md`.

*Offiziell Meta (Budgetplanung); Branchenpraxis (Saison) · [Budgetplanung](https://www.facebook.com/business/help/633318028866693), [Common Thread Collective](https://commonthreadco.com/blogs/coachs-corner/meta-cpms-are-about-to-spike-heres-your-6-week-window-to-get-ahead)*

### F-15 · Konto- und Trackingprobleme sehen aus wie Leistungsabfall

**Grundsatz:** Ein erreichtes Ausgabenlimit des Kontos oder einer Kampagne, ein von Meta gesetztes Tageslimit, Zahlungsprobleme, Ablehnungen (auch nachträglich bei laufenden Anzeigen) und Fehler bei Pixel oder Conversions API senken Spend oder zugeordnete Käufe, ohne dass das Adset schlechter geworden ist.

**Anwendung:** Vor einer Kürzung wegen eines Einbruchs prüfen: Liefert das Adset? Fallen alle Adsets eines Kontos gleichzeitig, oder fallen nur die Käufe bei normalem Spend und normalem Link-CPC, liegt der Fehler eher bei Konto oder Tracking. Dann nicht kürzen, sondern den Verdacht im Bericht nennen und den Entscheider bitten, Limits, Zahlung, Ablehnungen und Events Manager zu prüfen. Null-Spend ist kein Leistungssignal.

*Offiziell Meta · [Ausgabenlimit](https://www.facebook.com/business/help/998181913623584), [Anzeigen pausieren](https://www.facebook.com/business/help/204798856225114), [Anzeigenprüfung](https://www.facebook.com/business/help/236201204528536)*

## Entscheidungsweg je Adset

Orientierung, kein Schema. Ziel und Break-even sind die Werte des Produkts, gemessen nach dem Maßstab des Mandats.

| Lage | Naheliegende Entscheidung | Grundsätze |
|---|---|---|
| Über dem Ziel-ROAS, belastbar (genug Käufe über 7 Tage und seit der letzten Änderung) | Erhöhen; Schritt nach Abstand zum Ziel und Datenmenge; nach früheren Erhöhungen den Zusatzertrag prüfen | F-01, F-05, F-09 |
| Über dem Ziel, aber dünne Daten oder kurz nach einer Änderung | Halten oder behutsam erhöhen; Wirkung abwarten | F-01, F-02, F-03 |
| Zwischen Break-even und Ziel | Halten, bei klarer Tendenz behutsam in deren Richtung; das Mandat gewichtet (Wachstum, Neukunden) | F-08, F-11 |
| Unter Break-even, belastbar | Senken; deutlich darunter nach fairem Versuch pausieren | F-07, F-08 |
| Kaum oder keine Käufe nach fairem Versuch | Pausieren | F-08 |
| Neu oder in der Lernphase | Fairen Versuch ermöglichen; nur bei klarer Fehlentwicklung früher eingreifen | F-03, F-07, F-08 |
| Bislang gut, jetzt über Tage schwächer, Link-CPC steigt | Nicht erhöhen; senken, wenn nötig; Creative-Hinweis an den Entscheider | F-13 |
| Einbruch über das ganze Konto oder nur bei den Käufen | Erst Störung klären, nicht kürzen | F-15 |
| Aktions- oder Saisontage im Fenster | Störfaktor nennen, nicht darauf skalieren oder kürzen | F-14 |

## Was der Datenstand nicht zeigt

Lernstatus, Frequenz, CTR, CPM, Ermüdungsstatus, Lieferstatus und Ablehnungen sowie der Neukundenanteil stehen nicht im Datenstand. Ist eines davon für eine Entscheidung wichtig, den Verdacht im Bericht nennen und den Entscheider bitten, im Ads Manager oder in Triple Whale nachzusehen. Nicht raten.

## Nicht belegt oder strittig

- Eine Prozentgrenze, ab der eine Budgetänderung die Lernphase neu startet, gibt es offiziell nicht; die „20-%-Regel“ ist Folklore.
- Die Schwelle der Lernphase nennt Meta mit etwa 50 Ergebnissen pro Woche; Anbieter behaupten ohne Beleg niedrigere Werte für bestimmte Kampagnentypen.
- Multiplikatoren für einen fairen Versuch reichen je nach Quelle von 1,5× bis 5× Ziel-CPA.
- Die typische CPA-Steigerung beim Skalieren und Frequenz-Schwellen sind nicht belegt.
- Ein Meldeverzug von bis zu 72 Stunden stammt aus Quellen von 2021; ob er heute gilt, ist offen. Den Meldeverzug bei Triple Whale konnte die Recherche nicht prüfen.

## Pflege

Diese Datei gehört zum Kern und gilt für alle Startups. Startup-Eigenheiten gehören in Mandat und Learnings, nicht hierher. Änderungen nur auf Anweisung von Entscheider oder Systemverantwortlichem, mit Eintrag in [../docs/CHANGELOG.md](../docs/CHANGELOG.md). Beim Aktualisieren die Quellen neu prüfen und die Einordnung beibehalten.
