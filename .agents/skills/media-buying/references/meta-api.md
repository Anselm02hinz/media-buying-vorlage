# Meta Marketing API

Basis `https://graph.facebook.com/<META_API_VERSION>/`, Standard `v26.0` (Meta-Versionen laufen nach etwa einem Jahr aus; dann den Standard in `scripts/common.py` anheben oder `META_API_VERSION` setzen). Token in `META_ACCESS_TOKEN` (System-User-Token, nur die Konten aus `<startup>/startup.json`). Rechte: `ads_read`; `ads_management` erst, wenn der Schreibzugriff ausdrücklich freigeschaltet ist (siehe AGENTS.md).

## Lesen (`fetch_meta.py`)

| Abruf | Pfad | Wichtige Felder |
|---|---|---|
| Konto | `act_<id>` | `currency`, `timezone_name`, `account_status`, `spend_cap`, `amount_spent` |
| Adsets | `act_<id>/adsets` | `status`, `effective_status`, `daily_budget`, `campaign{daily_budget,…}`, `start_time`, `bid_strategy` |
| Insights | `act_<id>/insights?level=adset&time_increment=1` | `spend`, `inline_link_clicks`, `actions`, `action_values` |
| Änderungen | `act_<id>/activities` | `event_time`, `event_type`, `object_id`, `extra_data`, `actor_name`, `application_name` |

- Budgets kommen in Cent (`daily_budget: "8800"` = 88 in Kontowährung). Hat ein Adset kein eigenes Budget, liegt es auf Kampagnenebene (CBO); solche Adsets stehen im Bericht unter „Separat“ und sind nicht Teil des Plans.
- Insights mit `use_unified_attribution_setting=true`: gleiche Attribution wie im Ads Manager (je Adset eingestellt, z. B. 7-day click or 1-day view). Käufe/Umsatz aus `omni_purchase`, ersatzweise `purchase`.
- Link-CPC nur aus `inline_link_clicks`; `clicks` (alle Klicks) ist eine andere Kennzahl.
- `activities` liefert Budget-/Statusänderungen auch aus dem Ads Manager (z. B. die manuelle Umsetzung durch den Entscheider). Ist der Abruf nicht erlaubt, wird das als Lücke vermerkt; dann gilt die letzte Änderung aus früheren Plänen und der Akte.
- Vorher/Nachher liest `build_dataset.py` aus `extra_data` (JSON-Text mit `old_value`/`new_value`, Budgets in Cent). Ist es unlesbar, steht in der Phase „Änderung ohne bekannte Werte“; dann gelten die Werte aus früheren Plänen und der Akte.
- `actor_name` ist die Person, `application_name` das Werkzeug („Power Editor“ = Ads Manager). Meta liefert nie einen Grund.
- Der Verlauf ist unvollständig und nicht reproduzierbar: Derselbe Abruf kann Minuten später andere Einträge liefern, ganze Zeiträume können fehlen. `fetch_meta.py` ruft ihn deshalb am Stück und tageweise ab und führt beides ohne Doppelungen zusammen (Zahlen in `aktivitaeten_abruf`). Was dann noch fehlt, leitet `build_dataset.py` aus dem Vergleich mit dem letzten eigenen Datenstand ab: Eintrag ohne Person, Zeitpunkt = `updated_time` des Adsets (geschätzt), als Lücke und Hinweis je Adset gemeldet. Ohne früheren Datenstand meldet es nur, wenn das Budget nicht zum letzten Verlaufswert passt.
- Zeitzone und Währung der Konten müssen zu `startup.json` passen. Eine abweichende Kontozeitzone meldet `build_dataset.py` als Lücke.
- Kontozustand aus `account_status` (1 aktiv; 2 deaktiviert, 3 Zahlung offen, 101 geschlossen: keine Auslieferung), `disable_reason`, `spend_cap`/`amount_spent` (gleiche Einheit, nur das Verhältnis zählt). `build_dataset.py` zeigt ihn in der Übersicht und meldet gestoppte Konten und ein fast erreichtes Ausgabenlimit als Lücke.
- Kaufmessung: Hat ein Konto im Abrufzeitraum Spend, aber keinen einzigen Kauf, gilt die Messung als unklar (Lücke, ROAS `None`). Eingeschaltete Adsets mit `effective_status` `WITH_ISSUES`, `PENDING_BILLING_INFO`, `DISAPPROVED`, `PENDING_REVIEW` oder `IN_PROCESS` stehen in der Übersicht unter „Eingeschaltet, aber ohne Auslieferung“.
- Budgetfelder zählen nur mit einem Wert über 0 (`build_dataset.budget_of`).

## Prüfen bei der Einrichtung (`einrichtung.py`, nur lesend)

| Abruf | Zweck |
|---|---|
| `me/adaccounts` mit `account_status`, `disable_reason`, `spend_cap`, `amount_spent` | Welche Konten der Token sieht und in welchem Zustand |
| `act_<id>/adsets` (nur `ACTIVE`) mit `daily_budget`, `lifetime_budget`, `campaign{…}` | Budgetebene der aktiven Adsets: Adset-, Kampagnen- oder Laufzeitbudget |
| `act_<id>/insights?date_preset=last_28d` mit `spend`, `actions` | Ob Käufe gemessen werden |
| `act_<id>/adspixels` mit `last_fired_time` | Nur ohne gemessene Käufe: ob ein Pixel verbunden ist und wann er zuletzt auslöste |
| `act_<id>/campaigns` (nur mit `--kampagnen`) | Ziel und Budgetebene je Kampagne, Vorschläge für `separat` |

Die drei mittleren Abrufe sind beim ersten echten Lauf zu bestätigen (UNGEPRÜFT); schlägt einer fehl, meldet `einrichtung.py` einen Hinweis statt abzubrechen.

- Drosselung: Meta begrenzt Aufrufe je Werbekonto. In der Zugriffsstufe „Limited access“ (Standard jeder neuen App, früher „development access“; Antwortkopf `x-ad-account-usage`) sperrt Meta ein Konto nach wenigen Dutzend Aufrufen für einige Minuten (Fehlercode 17 u. a.). `fetch_meta.py` wartet dann einmal und wiederholt; scheitert ein Konto trotzdem, fehlt es als Lücke, die anderen Konten laufen weiter. Reicht das nicht, „Full access“ beantragen (App-Dashboard → App Review → Permissions and Features → Marketing API Access Tier).

## Schreiben (`plan.py ausfuehren`, nur mit Freigabe und `META_WRITE_ENABLED=1`)

`POST /<adset_id>` mit `daily_budget=<Cent>` und/oder `status=ACTIVE|PAUSED`. Vorher `GET /<adset_id>?fields=status,daily_budget`; weicht der Ist-Wert vom Vorherwert des Plans ab, wird die Zeile nicht geändert. Danach immer `plan.py pruefen`.
