"""Akte je Adset: Gedächtnis des Skills. Neuester Eintrag oben, Einträge werden nur ergänzt.

Ein Eintrag beginnt mit einer Kopfzeile, die eine unsichtbare Marke trägt, und endet mit `---`:

    ## 28.10.2026 11:30 · Vorschlag · A-20261028-001 <!-- akte:vorschlag:A-20261028-001 -->

    Text

    ---

Die Marke macht das Schreiben wiederholbar: Ein Eintrag mit derselben Marke wird nicht doppelt angelegt.
Nur ein noch nicht freigegebener Vorschlag darf ersetzt werden (`replace=True`).
"""
import re

from common import akte as akte_path, write_text

ENTRY_END = "\n---\n"
# Einträge, die erklären, warum etwas entschieden wurde; reine Meta-Änderungen zeigt die Übersicht ohnehin
GRUND_ARTEN = ("vorschlag", "entscheidung", "grund", "pruefung")


def marke(art, key):
    return f"<!-- akte:{art}:{key} -->"


def eintrag(zeit, titel, art, key, text):
    """zeit: ISO-Zeit mit Offset; titel: z. B. „Vorschlag · A-20261028-001“."""
    when = f"{zeit[8:10]}.{zeit[5:7]}.{zeit[:4]} {zeit[11:16]}".strip()
    return f"## {when} · {titel} {marke(art, key)}\n\n{text.strip()}\n{ENTRY_END}\n"


def schreiben(account_id, adset_id, name, entry, art, key, replace=False):
    """Setzt den Eintrag oben in die Akte. Gibt True zurück, wenn die Akte geändert wurde."""
    path = akte_path(account_id, adset_id)
    old = path.read_text(encoding="utf-8") if path.exists() else f"# {name or adset_id}\n\nKonto {account_id} · Adset {adset_id}\n"
    tag = marke(art, key)
    if tag in old:
        if not replace:
            return False
        start = old.rfind("\n## ", 0, old.index(tag)) + 1
        end = old.find(ENTRY_END, old.index(tag))
        end = len(old) if end < 0 else end + len(ENTRY_END) + 1
        new = old[:start] + entry + old[end:]
    else:
        new = entry + old
    if new == old:
        return False
    write_text(path, new)
    return True


def letzter_grund(account_id, adset_id):
    """ISO-Zeit des neuesten nachgetragenen Grundes (Eintrag „grund“, Schlüssel <adset>@<zeit>) oder None."""
    path = akte_path(account_id, adset_id)
    if not path.exists():
        return None
    times = re.findall(r"<!-- akte:grund:[^@]*@(\S+) -->", path.read_text(encoding="utf-8"))
    return max(times) if times else None


def auszug(account_id, adset_id, anzahl=2, laenge=280):
    """Die neuesten Einträge mit Begründungen (Vorschlag, Entscheidung, Grund, Prüfung, ältere Einträge ohne Marke),
    gekürzt und ohne Links, für die Übersicht. Reine Meta-Änderungen werden übersprungen."""
    path = akte_path(account_id, adset_id)
    if not path.exists():
        return []
    out = []
    for block in path.read_text(encoding="utf-8").split(ENTRY_END):
        block = block.strip()
        if not block.startswith("## "):
            continue
        art = re.search(r"<!-- akte:([a-z]+):", block)
        if art and art.group(1) not in GRUND_ARTEN:
            continue
        text = re.sub(r"<!--.*?-->", "", block)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # Links -> Linktext
        text = re.sub(r"[#*]+ ?", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        out.append(text if len(text) <= laenge else text[:laenge - 1].rstrip() + "…")
        if len(out) == anzahl:
            break
    return out
