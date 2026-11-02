# Einstieg für Claude Code

Es gelten dieselben Anweisungen wie für Codex:

@AGENTS.md

Für Media Buying, Budgetrunden, Budgetvorschläge und Freigaben immer den Skill `.agents/skills/media-buying/SKILL.md` vollständig lesen und Schritt für Schritt befolgen.

## Skripte ausführen

- Mac/Linux: `python3 .agents/skills/media-buying/scripts/<skript>.py …`
- Windows: `uv run --no-project --with tzdata python .agents/skills/media-buying/scripts/<skript>.py …` (`uv` liegt ggf. unter `~/.local/bin/uv`). Ohne `tzdata` fehlen unter Windows die Zeitzonendaten.
- Tests: dieselben Aufrufe mit `-m unittest discover .agents/skills/media-buying/tests`.
- Die Skripte lesen `.env` im Repository-Root selbst (z. B. `MEDIA_BUYING_MODUS=test`); Variablen nicht im Chat ausgeben.
