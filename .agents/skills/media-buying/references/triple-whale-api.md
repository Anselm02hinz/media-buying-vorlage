# Triple-Whale-API

Gegencheck zu Meta (ob und wie, regeln die Regeln des Startups). Einstellungen in `<startup>/startup.json` unter `triple_whale`: `aktiv` (false = ohne Triple Whale arbeiten), `shop_domain`, `modell`, `fenster`, `kanal`, `waehrung`. Zugang: `TRIPLEWHALE_API_KEY` (Header `x-api-key`, Scope Lesen); `TRIPLEWHALE_SHOP_DOMAIN` überschreibt bei Bedarf die Shop-Domain aus `startup.json`. Schlüssel testen: `GET https://api.triplewhale.com/api/v2/users/api-keys/me`.

## Abruf (`fetch_triple_whale.py`)

`POST https://api.triplewhale.com/api/v2/orcabase/api/sql` mit `shopId`, `query`, `period.startDate/endDate`. Die Abfrage summiert je Tag und Meta-Adset-ID Käufe (`orders_quantity`), Umsatz (`order_revenue`) und Spend aus `pixel_joined_tvf()` für den Kanal aus `startup.json` (Standard `facebook-ads`).

**Beim ersten Lauf bestätigen (UNGEPRÜFT):** Tabellen- und Spaltennamen, Modellname und Fenster. Stimmen Namen nicht, die Abfrage im Skript anpassen (`QUERY`) und im Kern-Changelog `.agents/skills/media-buying/docs/CHANGELOG.md` vermerken; Modell und Fenster mit dem Entscheider klären und in `startup.json` eintragen, nicht raten.

## Lesen der Werte

- TW-Werte sind in Shop-Währung (`triple_whale.waehrung`), Meta in Kontowährung (`waehrung`). ROAS ist je Quelle in sich konsistent; Spend nicht quellenübergreifend vergleichen, wenn die Währungen abweichen.
- Kein TW-Eintrag für ein Adset heißt „keine Zuordnung“, nicht null Käufe. Im Bericht als „TW –“.
- Käufe und Umsatz aus Meta und TW nie addieren; Abweichungen in beide Richtungen nennen.
