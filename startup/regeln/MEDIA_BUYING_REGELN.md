# Aktuelle Media-Buying-Regeln

Regelwerkstand: **0** · noch keine bestätigten Regeln. **Ohne Regeln hat der Skill keine Entscheidungsgrundlage.** Startregeln entstehen bei der Einrichtung: Die KI schlägt sie nach `references/regelvorlagen.md` des Skills vor, der Entscheider bestätigt oder passt an.

Hier stehen nur Regeln, die der Entscheider ausdrücklich vorgegeben hat, jeweils mit Quelle in `docs/quellen/`. Eigene Ableitungen der KI gehören in [REGELVORSCHLAEGE.md](REGELVORSCHLAEGE.md). Vor einer materiellen Änderung die alte Fassung in `docs/regelhistorie/` sichern und [AENDERUNGSVERLAUF.md](../docs/regelhistorie/AENDERUNGSVERLAUF.md) ergänzen.

## Register

| ID | Version | Titel | Gültig ab | Geltungsbereich | Quelle | Status |
|---|---|---|---|---|---|---|

## Format einer Regel

```markdown
## MB-0001 · v1 · <Titel>

**Wenn** <Lage>, **dann** <Handlung>.

- Quelle: Q-YYYYMMDD-NNN (Wortlaut des Entscheiders)
- Geltungsbereich, Ausnahmen, offene Begriffe (OFFEN)
```
