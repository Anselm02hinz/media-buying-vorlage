# Dokumentation einer Budgetrunde

Jede Information steht an einer Stelle; andere Dateien verlinken nur. **Ausnahme mit Absicht:** Plan und Akte enthalten teils dasselbe, aus zwei Blickwinkeln. Der **Plan** dokumentiert eine Runde für die Menschen (Auftrag, was vorgeschlagen, entschieden und laut Meta tatsächlich geändert wurde, jeweils warum). Die **Akte** ist das Gedächtnis des Skills je Adset (Historie und Gründe, vor allem Korrekturen des Entscheiders). Der Skill liest beim Entscheiden die Akten, nicht die Pläne. Alle Pfade liegen im Startup-Ordner `<startup>/`, der einzige Ordner im Repository-Root mit einer `startup.json` (in der Vorlage `startup/`, sonst meist nach dem Startup benannt, z. B. `acme/`; die Skripte finden ihn selbst).

## Ablage im Startup-Ordner

```
<startup>/
├── startup.json          Stammdaten für die Skripte (Name, Rollen, Konten, Währung, Zeitzone, Zielwerte, Mindestbudget, Triple Whale)
├── README.md             Profil: Konten, Daten und Attribution, Zielwerte mit Quellen, Befugnisse, Abweichungen von AGENTS.md
├── AKTUELL.md            Einstieg jeder Sitzung
├── LEARNINGS.md          wie der Entscheider entscheidet (geht dem allgemeinen Fachwissen vor)
├── regeln/               MANDAT.md (Ziel, Maßstab, Leitplanken), Prüfreihenfolge, ggf. Systemregeln
├── akten/                Akte je Adset: meta_<konto>_<adset>.md (Gedächtnis des Skills)
├── runden/YYYY-MM-DD/    alles einer Runde: Datenstand, Übersicht, Bericht, Plan, Verifikation; rohdaten/ nur lokal
├── testdaten/            testdaten.json (erfunden); testlaeufe/ mit denselben Unterordnern runden/ und akten/
└── docs/                 liest der Skill in einer Runde nicht: quellen/ (Originalquellen Q-…), regelhistorie/
                          (alte Fassungen von Mandat und Leitplanken, Änderungsverlauf), TODO.md, CHANGELOG.md
```

Faustregel: Was der Skill in einer normalen Runde liest oder schreibt, liegt direkt in `<startup>/` oder in `regeln/`, `akten/`, `runden/`. Was nur belegt, beschreibt oder den Verlauf festhält, liegt in `docs/`. Verweise möglichst über IDs (`R-…`, `A-…`, `D-…`, `Q-…`, `MB-…` für Leitplanken, `F-…` für Fachwissen, `L-…`) statt über Pfade; IDs bleiben bei einem Umzug gültig.

## Was wo steht

| Inhalt | Datei | Erstellt durch |
|---|---|---|
| API-Rohdaten, erster Entscheidungsentwurf | `<startup>/runden/YYYY-MM-DD/rohdaten/` (nicht versioniert, nur vorübergehend) | Skripte, KI |
| Datenstand | `<startup>/runden/YYYY-MM-DD/D-YYYYMMDD-NNN-budget.json` | `build_dataset.py` |
| Übersicht (Arbeitsgrundlage der KI: Kennzahlen, Tagesreihe, Änderungen, Akten-Auszug je aktivem Adset) | `<startup>/runden/YYYY-MM-DD/D-YYYYMMDD-NNN-uebersicht.md` | `build_dataset.py` |
| Bericht | `<startup>/runden/YYYY-MM-DD/R-YYYYMMDD-NNN-budgetvorschlaege.html` | `render_report.py` |
| Plan (ID `A-YYYYMMDD-NNN`): Auftrag (`bericht.auftrag`), Vorschlag des Skills mit Grund (`vorschlag`), Entscheidung bzw. Korrektur mit Grund (`entscheidung`, `gruende`), Umsetzung laut Meta (`umsetzung_meta`, `ausserhalb_plan`), Berichtstexte, Freigabe mit Wortlaut, Ausführung, Prüfstatus | `<startup>/runden/YYYY-MM-DD/AUSFUEHRUNGSPLAN_YYYYMMDD_BUDGET.json` (Dokumentation der Runde; Korrekturen nur über `plan.py korrigieren`) | `render_report.py`, `plan.py`, `build_dataset.py` (Abgleich), KI |
| Verifikation | `<startup>/runden/YYYY-MM-DD/VERIFIKATION_YYYYMMDD_BUDGET.json` | `plan.py pruefen` |
| Akte je Adset: Änderungen laut Meta mit Person und Einordnung, Vorschläge mit Grund und Zahlen, Entscheidungen und Korrekturen mit Grund, nachgetragene Gründe, Prüfergebnisse | `<startup>/akten/meta_<konto>_<adset>.md` (neuester Eintrag oben, nur ergänzen) | `build_dataset.py`, `render_report.py`, `plan.py freigeben/begruenden/pruefen` |
| Aktuelle Lage, letzte Sitzungen, offene Punkte für die nächste Runde (Einstieg jeder Sitzung) | `<startup>/AKTUELL.md` | KI |
| Begründungsmuster des Entscheiders, nach Themen | `<startup>/LEARNINGS.md` | KI, nur bei Neuem |
| Offene Aufgaben zum Aufbau, Vorschläge für den Kern | `<startup>/docs/TODO.md` | KI |
| Änderungen am Startup-Ordner bzw. am Kern | `<startup>/docs/CHANGELOG.md` bzw. `.agents/skills/media-buying/docs/CHANGELOG.md` | KI |
| Chronik der Sitzungen | Git-Commits (je Sitzung ein Commit mit aussagekräftiger Nachricht) | KI |

Tagesprotokolle und Änderungsdatensätze gibt es nicht: Was eine Runde betrifft, steht in Plan, Bericht und Akten; Änderungen am System in den Changelogs; offene Punkte und die letzten Sitzungen in AKTUELL.md; die Chronik in Git.

IDs: Bericht `R-YYYYMMDD-NNN` (nächste freie Nummer des Tages) und Plan `A-YYYYMMDD-NNN` (gleiche Nummer) vergibt `render_report.py`; Datenstand `D-…` vergibt `build_dataset.py`. Zeiten in der Zeitzone aus `startup.json` mit Offset. Rücknahme einer Runde: auf die Vorherwerte im Plan, nur nach neuer Freigabe. Die Wirkungskontrolle macht die nächste Runde (Abgleich, Phase seit letzter Änderung in der Übersicht).

## Akte

Die Skripte schreiben die Akten; die KI ändert sie nicht von Hand. Jeder Eintrag trägt eine unsichtbare Marke (`<!-- akte:<art>:<schlüssel> -->`), damit ein wiederholter Lauf nichts doppelt einträgt. Arten: `meta` (Änderung laut Meta mit Person, Werkzeug und Einordnung „wie entschieden“, „abweichend“ oder „ohne Plan“), `vorschlag` (wird bis zur Freigabe beim Neu-Rendern ersetzt), `entscheidung`, `grund`, `pruefung`. Fortgeschrieben werden alle Adsets, die aktiv sind oder im Abrufzeitraum geliefert haben.

## AKTUELL.md

Einstieg jeder Sitzung. Keine Verlaufseinträge anhängen, sondern die Abschnitte überschreiben:

- **Letzte Budgetrunde:** Datum, Status, Links, Budgetsummen je Konto.
- **Letzte Sitzungen:** je Sitzung 1–2 Zeilen (Datum, was passiert ist, Entscheidungen im Gespräch, die sonst nirgends stehen, z. B. Rückfragen an den Entscheider und seine Antworten); nur die letzten fünf, ältere löschen (Verlauf in Git). Am Ende jeder Sitzung ergänzen, auch wenn sie ohne Freigabe oder mit einem Abbruch endet.
- **Für die nächste Runde:** offene Wirkungskontrollen, Haltefristen und Einzelfallanweisungen des Entscheiders, offene Fragen, bekannte Störungen und Kontext (z. B. Kampagnenbudgets).

Erledigte Hinweise löschen. Werte je Adset und Wortlaute von Auftrag und Freigabe stehen im Plan; hier nur verlinken.

## Learnings

Eine Datei `<startup>/LEARNINGS.md` mit drei Abschnitten: **Bestätigt**, **Kandidaten**, **Überholt**. Learnings halten fest, wie der Entscheider entscheidet: wo Mandat und Fachwissen Spielraum lassen oder wo er anders gewichtet als das allgemeine Fachwissen (z. B. wie stark er skaliert, wann er einem Test mehr Zeit gibt). Bestätigte Learnings gehen dem Fachwissen vor, wirken aber nie gegen Mandat oder Leitplanken. Nur bestätigte Learnings beeinflussen Vorschläge.

### Format

```markdown
### L-NN · <Muster in einem Satz>
Status: Kandidat | bestätigt (<Name>, <Datum>, „<Wortlaut>“) | überholt (<Datum>, <Grund>)
Bezug: <Fachwissen-ID, die es präzisiert oder von der es abweicht, bzw. Teil des Mandats>
Wann: <Situation mit prüfbaren Merkmalen aus der Übersicht>
<Name des Entscheiders> entscheidet: <was der Entscheider in dieser Situation tut>
Begründung: <Wortlaut des Entscheiders, falls genannt>
Belege: <Datum, Adset, Vorschlag Skill → Entscheidung, Plan-ID/Q-ID>
Gegenbeispiele: <Fälle, in denen er anders entschied>
Wirkung: offen | <Auswertung>
```

IDs fortlaufend (L-01, L-02 …), nie neu vergeben.

### Entstehung

1. **Einzelfall:** Jede Korrektur (`plan.py korrigieren`), jeder Grund (`plan.py begruenden`) und jede Abweichung laut Meta steht in Plan und Akte. Ein Einzelfall ist noch kein Learning.
2. **Kandidat:** Am Ende der Runde (Schritt 8) die Korrekturen dieser Runde und die neuen Gründe in den Akten durchgehen. Zeigen mindestens zwei Fälle dasselbe Muster, oder nennt der Entscheider einen allgemeinen Grund, als Kandidat eintragen (Format oben) oder bei einem bestehenden Learning als Beleg ergänzen.
3. **Rückfrage:** Im nächsten Bericht höchstens ein bis zwei Kandidaten als Frage an den Entscheider (`notizen`, „Fragen an den Entscheider“), konkret formuliert („Mir fällt auf: … Soll ich das künftig so vorschlagen?“).
4. **Bestätigt:** Antwortet der Entscheider zustimmend, auch eingeschränkt („ja, aber nur wenn …“), Status mit Name, Datum und Wortlaut setzen und die Einschränkung unter „Wann“ übernehmen. Formuliert er selbst einen allgemeinen Grund („künftig …“, „grundsätzlich …“), gilt das als Bestätigung.
5. **Pflege:** Neue passende Fälle als Beleg ergänzen. Korrigiert der Entscheider einen Vorschlag, der sich auf ein Learning stützte, als Gegenbeispiel eintragen; bei wiederholten Gegenbeispielen nachfragen und gegebenenfalls „überholt“ setzen. Lehnt er einen Kandidaten ab, „überholt“ mit Grund.
6. **Leitplanke:** Will der Entscheider ein Learning als harte Grenze, wird es eine Leitplanke im Mandat (`AGENTS.md`, „Mandat und Leitplanken“).

Einzelfall-Beobachtungen zu einem Adset gehören in dessen Akte, nicht in die Learnings.
