# Anleitung · Media-Buying-Skill einrichten und nutzen

## Was ist das?

Der Skill macht jeden Tag Budgetvorschläge für eure Meta-Adsets: erhöhen, senken, pausieren oder halten, jeweils mit Begründung und Zahlen. Er läuft in **Codex** (ChatGPT) oder **Claude Code** (B3a) und liest eure Werbedaten nur. **Er ändert nichts an euren Konten:** Du entscheidest, gibst frei und setzt im Ads Manager selbst um.

> **Wichtig: Der Skill arbeitet wie ein Media-Buying-Dienstleister nach eurem Ziel.** Bei der Einrichtung schreibst du in eigenen Worten auf, was ihr mit den Meta-Ads erreichen wollt, zum Beispiel: „Mit allen Adsets den Ziel-ROAS erreichen. Was nach ernsthaften Versuchen nicht läuft, herunterfahren oder abschalten. Was gut läuft, so weit wie möglich pushen.“ Starre Regeln wie „ab ROAS X um 20 % erhöhen“ brauchst du nicht: Wie das Ziel am besten erreicht wird, entscheidet der Skill in jeder Runde mit Media-Buying-Fachwissen und allen Daten, und er begründet es. Du gibst frei oder korrigierst; aus deinen Korrekturen lernt er deinen Stil. Ändern kannst du das Ziel jederzeit.

So läuft die Einrichtung:

| Schritt | Was passiert | Wer |
|---|---|---|
| **Teil A** | ZIP entpacken, in GitHub hochladen, Codex verbinden | du, mit dieser Anleitung |
| **Chat 1** | Meta-Zugang anlegen, in Codex eintragen | du, Codex führt dich |
| **Chat 2** | Werbekonten wählen, Zielwerte nennen, **euer Ziel festhalten**, sichern | du, Codex führt dich |

Du brauchst keine Programmierkenntnisse. Ab Teil A, Schritt 5 führt dich Codex Schritt für Schritt; Teil B brauchst du nur zum Nachlesen.

---

## Teil A · Vorbereitung (ohne Codex)

### A1 · Das brauchst du

- [ ] **ChatGPT mit Codex:** Abo Plus, Pro, Business, Enterprise oder Edu. Bei Enterprise muss ein Admin „Use Codex in the cloud“ freischalten.
- [ ] **GitHub-Konto:** kostenlos auf [github.com](https://github.com).
- [ ] **Die ZIP-Datei** mit dem Skill, die du per Mail bekommen hast.
- [ ] **Admin-Zugang zum Meta Business-Portfolio** (Business Manager), dem eure Werbekonten gehören, oder eine Person mit diesem Zugang, die dir kurz hilft.
- [ ] Nur wenn ihr Triple Whale nutzt: Zugang als **Owner oder Admin**.
- [ ] **Kurz überlegen** (Codex fragt danach): Ab welchem ROAS ist euer Produkt profitabel (Break-even)? Welchen ROAS strebt ihr an (für alle Produkte gleich oder je Produkt)? Was wollt ihr mit euren Meta-Ads erreichen, und was soll mit Adsets passieren, die gut oder schlecht laufen?

> **Internetzugang:** Der Skill ruft `graph.facebook.com` (Meta) und, nur mit Triple Whale, `api.triplewhale.com` auf. In der Codex-Umgebung und in Claude Code im Web sind diese Domains gesperrt, bis du sie erlaubst: Codex B3, Schritt 3; Claude Code B3a. Fehlen sie, meldet der Skill „nicht erreichbar“.

### A2 · ZIP entpacken und versteckte Dateien sichtbar machen

1. Die ZIP-Datei doppelklicken. Es entsteht ein Ordner, z. B. `media-buying-vorlage`.
2. **Wichtig:** Einige Dateien beginnen mit einem Punkt und sind deshalb versteckt. Darunter ist der Ordner **`.agents`**, das ist der Skill selbst.
   - **Mac:** Im Finder den Ordner öffnen und **Cmd + Shift + .** (Punkt) drücken. Die versteckten Dateien erscheinen blass.
   - **Windows:** Sie werden normalerweise angezeigt. Falls nicht: Explorer → **Ansicht** → **Anzeigen** → **Ausgeblendete Elemente**.
3. Prüfe: Im Ordner siehst du `.agents`, `.env.example`, `.gitignore`, `AGENTS.md`, `ANLEITUNG.md`, `CLAUDE.md`, `README.md` und `startup`.

### A3 · GitHub: privates Repository anlegen und Dateien hochladen

1. Auf [github.com](https://github.com) anmelden, oben rechts auf **+** → **New repository**.
2. **Repository name:** z. B. `media-buying` (ohne Leerzeichen). **Visibility:** **Private**. „Add README“ aus lassen, bei .gitignore und License nichts wählen. → **Create repository**.
3. Auf der nächsten Seite auf **uploading an existing file** klicken (oder später: **Add file** → **Upload files**).
4. Im entpackten Ordner **alles markieren** (Mac: Cmd + A, Windows: Strg + A), auch die versteckten Dateien, und ins Browserfenster ziehen. **Den Inhalt ziehen, nicht den Ordner selbst.** Ist auf dem Mac eine Datei `.DS_Store` dabei, ist das egal.
5. Warten, bis alle Dateien gelistet sind, dann unten **Commit changes**.
6. **Kontrolle:** Auf der Startseite deines Repositorys stehen direkt (nicht in einem Unterordner) `.agents`, `startup`, `.env.example`, `.gitignore`, `AGENTS.md`, `ANLEITUNG.md`, `CLAUDE.md`, `README.md`.
   - Siehst du nur einen einzigen Ordner wie `media-buying-vorlage`? Dann ist der Ordner statt seines Inhalts hochgeladen. Repository löschen (**Settings** → ganz unten **Delete this repository**) und Schritte 1–5 wiederholen.
   - Fehlen `.agents`, `.gitignore` oder `.env.example`? Versteckte Dateien einblenden (A2) und diese über **Add file** → **Upload files** nachladen.

### A4 · Codex mit dem Repository verbinden

1. [chatgpt.com/codex](https://chatgpt.com/codex) öffnen.
2. Eine neue Aufgabe beginnen, bei **Work in** die Option **Cloud** wählen, dann **Select environment** → **Create environment**.
3. Dein Repository auswählen. Fragt Codex nach GitHub: **Connect GitHub**. GitHub zeigt dann die App **ChatGPT Codex Connector**: dein Konto wählen, **Only select repositories**, dein Repository auswählen, **Install**.
4. **Get started.** Codex schaut sich das Repository an und richtet die Umgebung selbst ein. Rückfragen beantworten. Zugangsdaten hast du noch keine, die kommen in Chat 1.
5. Den Setup-Bericht ansehen und **Publish** klicken. Bei „Environment published“: **Start a new task**.

### A5 · Ersten Chat starten

In der neuen Aufgabe (Work in: Cloud, deine Umgebung) schreibst du:

> **Richte den Media-Buying-Skill ein und führe mich Schritt für Schritt.**

Ab hier führt dich Codex. Es meldet sich nach jedem Schritt und sagt, was als Nächstes kommt. Den Stand kannst du jederzeit abfragen: „Wie ist der Stand der Einrichtung?“

---

## Teil B · Klickwege zum Nachlesen

Codex führt dich durch diese Schritte. Die Oberflächen von Meta, GitHub und Codex ändern sich öfter; weichen Bezeichnungen ab, beschreib Codex einfach, was du siehst.

### B1 · Meta: Zugang nur zum Lesen (Systemnutzer-Token)

Du brauchst dafür Admin-Rechte im Business-Portfolio. Das Ergebnis ist ein Token: ein langer Schlüssel, mit dem der Skill eure Werbedaten **lesen**, aber nicht ändern kann.

**App anlegen (einmalig)**
1. [developers.facebook.com/apps/creation](https://developers.facebook.com/apps/creation/) öffnen, mit dem Facebook-Konto, das Admin im Business-Portfolio ist.
2. App-Name (z. B. „Media Buying Reporting“) und Kontakt-E-Mail eingeben.
3. Als Anwendungsfall (Use case) **Measure ad performance data with Marketing API** wählen.
4. Euer **Business-Portfolio** verbinden.
5. Durchklicken bis **Go to dashboard**. Eine Prüfung durch Meta (App Review) ist nicht nötig.

**Systemnutzer anlegen**

6. [business.facebook.com/settings](https://business.facebook.com/settings) → **Nutzer** → **Systemnutzer** (Users → System users) → **Hinzufügen** (+ Add).
7. Name, z. B. „Media Buying Skill“. Rolle **Mitarbeiter** (Employee), nicht Admin → **Systemnutzer erstellen**.

**Zugriff geben**

8. Den Systemnutzer anklicken → **Assets zuweisen** (Assign assets) → **Apps** → eure App → **App verwalten** (Manage app) → zuweisen.
9. Nochmal **Assets zuweisen** → **Werbekonten** (Ad accounts) → die Werbekonten, um die es geht → **Teilzugriff** (Partial access) mit nur **Leistung ansehen** (View performance) → zuweisen.

**Token erzeugen**

10. Beim Systemnutzer: **Neuen Token generieren** (Generate new token).
11. Eure App auswählen. Ablauf: **Nie** (Never); Meta bietet sonst nur 60 Tage an. Aus Sicherheitsgründen erneuerst du den Token trotzdem **alle 6 Monate** (B6). Trag dir gleich eine Kalender-Erinnerung in 6 Monaten ein; der Skill erinnert dich zusätzlich 14 Tage vorher.
12. Berechtigungen: **nur `ads_read`** anhaken, nicht `ads_management`.
13. **Token generieren** und kopieren. **Er wird nur einmal angezeigt.** Nicht in den Chat einfügen, sondern direkt in B3 eintragen.

### B2 · Triple Whale: API-Key (nur wenn ihr Triple Whale nutzt)

1. [app.triplewhale.com/api-keys](https://app.triplewhale.com/api-keys) öffnen (auch über **Settings** → **API Keys**).
2. **Generate**. Beschreibung „Media Buying Skill“. Nur Leserechte wählen: **Pixel Attribution: Read** und **Summary Page: Read**, falls angeboten auch **Data Out**. Keine Rechte mit „Write“.
3. **Generate** und den Key kopieren. **Er wird nur einmal angezeigt.**
4. **Shop-Domain** notieren: Sie steht in der Adresszeile von Triple Whale hinter `shop-id=`, z. B. `euershop.myshopify.com`.

Der Key hängt an deinem Triple-Whale-Nutzer. Wirst du aus dem Shop entfernt, funktioniert er nicht mehr.

### B3 · Codex-Umgebung: Zugänge und Internet eintragen

1. In Codex **Settings** → **Codex Cloud** → **Environments** → deine Umgebung → **…** → **Edit**.
2. **Environment variables** → **Manage** → hinzufügen:

   | Name | Wert |
   |---|---|
   | `META_ACCESS_TOKEN` | dein Meta-Token aus B1 |
   | `TRIPLEWHALE_API_KEY` | nur mit Triple Whale: Key aus B2 |
   | `TRIPLEWHALE_SHOP_DOMAIN` | nur mit Triple Whale: z. B. `euershop.myshopify.com` |

   Nicht unter „HTTP secrets“ eintragen. `META_WRITE_ENABLED` nicht anlegen.
3. **Public internet access:** „Enable all public internet access“ aus lassen. Unter **Additional allowed domains** eintragen: `graph.facebook.com` und, nur mit Triple Whale, `api.triplewhale.com`.
4. **Republish** klicken.
5. Einen **neuen Chat** starten (Work in: Cloud, deine Umgebung) und schreiben: **„Weiter mit der Einrichtung.“** Neue Werte sieht Codex erst in einem neuen Chat.

### B3a · Claude Code statt Codex: Zugänge und Internet eintragen

Nur wenn ihr den Skill in Claude Code nutzt. Die Bezeichnungen sind die der englischen Oberfläche.

**Claude Code im Web** ([claude.ai/code](https://claude.ai/code))

1. Unter dem Eingabefeld die Umgebung anklicken. Unter **Cloud** mit der Maus auf deine Umgebung zeigen und rechts auf das Einstellungssymbol klicken. Es öffnet sich **Edit cloud environment**.
2. **Environment variables:** je Zeile `NAME=Wert` eintragen: `META_ACCESS_TOKEN=…` (Token aus B1), nur mit Triple Whale auch `TRIPLEWHALE_API_KEY=…` (B2) und `TRIPLEWHALE_SHOP_DOMAIN=…`. Nicht unter „Network secrets“ eintragen (die Skripte brauchen den Wert selbst). `META_WRITE_ENABLED` nicht anlegen. Wer die Umgebung nutzt, kann diese Werte lesen; die Umgebung deshalb nicht mit anderen teilen.
3. **Network access:** **Custom** wählen. Unter **Allowed domains** je Zeile eine Domain eintragen: `graph.facebook.com` und, nur mit Triple Whale, `api.triplewhale.com`. Das Häkchen bei **Also include default list of common package managers** setzen. Die Standardstufe **Trusted** reicht nicht, sie enthält weder Meta noch Triple Whale; **Full** ist nicht nötig.
4. **Save changes**, dann eine **neue Sitzung** starten und schreiben: **„Weiter mit der Einrichtung.“** Neue Zugangsdaten sieht Claude erst in einer neuen Sitzung.

**Claude Code auf dem eigenen Rechner** (Terminal, VS Code, Desktop-App)

- **Zugänge:** im Repository-Ordner `.env.example` nach `.env` kopieren und die Werte eintragen. `.env` wird nicht hochgeladen.
- **Internet:** ohne Sandbox frei, nichts zu tun. Ist die Sandbox eingeschaltet (`/sandbox`), die Domains in `~/.claude/settings.json` erlauben (unter Windows gibt es die Sandbox nur mit WSL):

  ```json
  {"sandbox": {"network": {"allowedDomains": ["graph.facebook.com", "api.triplewhale.com"]}}}
  ```

### B4 · Änderungen sichern: Pull Request erstellen und mergen

Codex arbeitet in einer Kopie. Was es ändert (Einrichtung, Akten, Berichte), kommt erst in dein Repository, wenn du es übernimmst. **Sonst ist es im nächsten Chat weg.** Darum am Ende jeder Sitzung:

1. Im Chat schreiben: **„Erstelle einen Pull Request.“** Codex nennt dir einen Link.
2. Den Link öffnen (GitHub) → **Merge pull request** → **Confirm merge**.

### B5 · Bericht ansehen

Codex fasst die wichtigsten Zahlen im Chat zusammen. Den ganzen Bericht öffnest du so:

1. Im Pull Request auf **Files changed**.
2. Die Datei `…-budgetvorschlaege.html` suchen → **…** → **View file** → **Download raw file** (Pfeil nach unten).
3. Die heruntergeladene Datei doppelklicken; sie öffnet sich im Browser.

### B6 · Meta-Token erneuern (alle 6 Monate)

1. Den alten Token widerrufen: in den Business-Einstellungen beim Systemnutzer **Token widerrufen** (Revoke tokens). Das **vor** dem neuen Token tun, damit nicht versehentlich der neue widerrufen wird.
2. Einen neuen Token erzeugen: B1, Schritte 10–13.
3. In der Codex-Umgebung bei `META_ACCESS_TOKEN` den neuen Wert eintragen und **Republish** klicken (B3; Claude Code: B3a, Schritt 2).
4. Neuer Chat: **„Ich habe den Meta-Token heute erneuert.“** Codex prüft den Zugang und trägt das Datum für die nächste Erinnerung ein. Danach sichern (B4).

---

## Teil C · Jeden Tag

1. Neuer Chat (Work in: Cloud, deine Umgebung): **„Mach mein Media Buying für heute.“**
2. Codex holt die Daten und schlägt je Adset vor: erhöhen, senken, pausieren oder halten, mit Begründung. Den ganzen Bericht siehst du nach B5.
3. **Du entscheidest.** Korrekturen einfach schreiben, am besten mit Grund: „A03 lieber 40 €, weil …“. Aus deinen Gründen lernt der Skill deinen Stil, aber erst nach deiner Bestätigung.
4. **Freigeben** mit einem klaren Satz, z. B. „Go, so umsetzen.“ Ohne klares Go passiert nichts.
5. Die Änderungen **selbst im Ads Manager** umsetzen.
6. „**Prüf, ob die Budgets umgesetzt sind.**“
7. **Sichern** (B4).

Zwischendurch geht auch: „Wie laufen die Adsets?“ oder „Was soll ich kürzen?“

**Ziel oder Grenzen ändern:** einfach schreiben, z. B. „Diesen Monat zählt Wachstum mehr als der ROAS.“ oder, als feste Grenze, „Erhöhe nie mehr als 15 % auf einmal.“ Codex zeigt dir alte und neue Fassung und trägt die neue nach deinem Ja ein; die alte bleibt im Verlauf erhalten.

**Wichtig**
- Der Skill liest nur. Geändert wird nur von dir im Ads Manager.
- Freigeben darf nur der Entscheider (bei der Einrichtung festgelegt). Schweigen ist keine Freigabe.
- Zugangsdaten nie in den Chat schreiben.
- Am Ende jeder Sitzung mergen (B4), sonst fehlt beim nächsten Mal das Gedächtnis des Skills.

---

## Teil D · Wenn etwas hakt

| Meldung oder Problem | Was tun |
|---|---|
| „Upload unvollständig“, `.agents` oder `.gitignore` fehlt | Versteckte Dateien einblenden (A2) und nachladen (A3, Schritt 6), dann neuer Chat |
| Codex kennt den Skill nicht | Liegt `AGENTS.md` direkt auf der Startseite des Repositorys? Sonst A3, Schritt 6 |
| „META_ACCESS_TOKEN fehlt“ | B3, dann neuer Chat |
| „graph.facebook.com nicht erreichbar“ oder „api.triplewhale.com nicht erreichbar“ | Domain in der Umgebung erlauben: Codex B3, Schritt 3 und **Republish**; Claude Code B3a. Dann neuer Chat |
| „Meta-Token ungültig oder abgelaufen“ | B1, Schritte 10–13, dann B3 |
| „Konto … nicht freigegeben“ oder „Berechtigungsfehler“ | B1, Schritt 9: Werbekonto dem Systemnutzer zuweisen |
| „Meta drosselt das Werbekonto“ | Nichts tun; das Skript wartet etwa 5 Minuten und versucht es erneut |
| „startup.json enthält noch Beispielwerte“ | Einrichtung nicht abgeschlossen: „Weiter mit der Einrichtung“ |
| „Noch kein Ziel im Mandat“ | „Weiter mit der Einrichtung“: Codex fragt nach eurem Ziel und schreibt es nach deinem Ja auf |
| „Erinnerung: Meta-Token erneuern“ | B6 |
| Änderungen vom letzten Mal fehlen | Pull Request nicht gemergt: B4 |

---

## Gut zu wissen

- **Was wo liegt:** Der Ordner `startup/` heißt nach der Einrichtung wie euer Startup. Darin liegt alles von euch: Einstellungen, euer Ziel (Mandat), Learnings, Akten je Adset und alle Runden. Der Ordner `.agents/` ist der Skill selbst; bitte nicht ändern.
- **Neue Versionen** des Skills bekommt ihr vom Systemverantwortlichen. Ersetzt werden nur `.agents/` und die Dateien im Hauptordner, nie euer Startup-Ordner.
- **Schreibzugriff:** Der Skill könnte freigegebene Budgets technisch auch selbst umsetzen. Das ist gesperrt und bleibt es, bis Entscheider oder Systemverantwortlicher es bewusst freischalten.
- **Platzhalter:** Namen und Zahlen der Vorlage gelten für kein echtes Startup: Beispielwerte in `startup.json` (`"beispiel": true`), OFFEN in Profil und Regeln, die Testdaten sowie Beispielzahlen in Skill, Referenzen und Tests (z. B. Budgets wie 88 €, Leitplanken-IDs wie `MB-0001 v1`, Fachwissen-IDs wie `F-04`, Learning-IDs wie `L-03`). Echte Werte trägt Codex bei der Einrichtung ein, erst nach Bestätigung durch den Entscheider.
