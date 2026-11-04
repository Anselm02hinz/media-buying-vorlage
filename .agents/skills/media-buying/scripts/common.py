"""Gemeinsame Helfer: Pfade, Startup-Daten, Zugangsdaten, HTTP, Zeitfenster. Nur Standardbibliothek.

Alles Startup-Spezifische liegt im Startup-Ordner `<startup>/`: dem einzigen Ordner im Repository-Root mit einer
`startup.json` (in der Vorlage `startup/`, sonst meist nach dem Startup benannt). Ablage dort: `akten/` (Akte je
Adset), `runden/<YYYY-MM-DD>/` (alles einer Runde, Rohdaten in `rohdaten/`).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")
SKILL_DIR = Path(__file__).resolve().parents[1]


def find_root():
    for p in SKILL_DIR.parents:
        if (p / "AGENTS.md").exists():
            return p
    raise SystemExit("Repository-Root (AGENTS.md) nicht gefunden.")


def find_startup(root):
    """Der Startup-Ordner: der einzige Ordner direkt im Repository-Root mit einer `startup.json`."""
    found = sorted(p.parent for p in root.glob("*/startup.json"))
    if not found:
        raise SystemExit("Kein Startup-Ordner (Ordner im Repository-Root mit startup.json). Für ein neues Startup siehe "
                         "ANLEITUNG.md.")
    if len(found) > 1:
        raise SystemExit(f"Mehrere Ordner mit startup.json: {', '.join(p.name for p in found)}. Erlaubt ist genau einer.")
    return found[0]


ROOT = find_root()
STARTUP_DIR = find_startup(ROOT)
REQUIRED = ("name", "entscheider", "zeitzone", "waehrung", "waehrungszeichen", "mindestbudget", "konten")


def load_startup():
    path = STARTUP_DIR / "startup.json"
    name = f"{STARTUP_DIR.name}/startup.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"{name} ist kein gültiges JSON (Zeile {e.lineno}): {e.msg}") from None
    missing = [k for k in REQUIRED if data.get(k) in (None, "", {})]
    if missing:
        raise SystemExit(f"{name}: Pflichtfelder fehlen: {', '.join(missing)}")
    for key, acc in data["konten"].items():
        if not acc.get("id") or not acc.get("prefix"):
            raise SystemExit(f"{name}: Konto {key!r} braucht 'id' und 'prefix'.")
    return data


STARTUP = load_startup()
ACCOUNTS = STARTUP["konten"]
CURRENCY, CURRENCY_SIGN = STARTUP["waehrung"], STARTUP["waehrungszeichen"]
TW = {"aktiv": False, **(STARTUP.get("triple_whale") or {})}
# Keine Verkaufs-Adsets (z. B. Follower): nicht im Plan, keine Mindestbudget-Prüfung, im Bericht unter „Separat“.
SEPARAT = {"kampagnen": {}, "adsets": {}, **(STARTUP.get("separat") or {})}


def separat_name(adset_id, campaign_id):
    return SEPARAT["adsets"].get(adset_id) or SEPARAT["kampagnen"].get(campaign_id)


# Werbekonto laut Meta (`account_status`); bei 2, 3 und 101 liefert das Konto nicht aus.
KONTOSTATUS = {1: "aktiv", 2: "deaktiviert", 3: "Zahlung offen", 7: "in Prüfung", 9: "Kulanzzeit", 101: "geschlossen"}
KONTO_GESTOPPT = (2, 3, 101)
# Adset eingeschaltet (`status` ACTIVE), liefert laut Meta aber nicht aus (`effective_status`)
LIEFERPROBLEME = {"WITH_ISSUES": "mit Problemen laut Meta", "PENDING_BILLING_INFO": "Zahlungsdaten fehlen",
                  "DISAPPROVED": "abgelehnt", "PENDING_REVIEW": "in Prüfung", "IN_PROCESS": "wird verarbeitet"}

try:
    TZ = ZoneInfo(STARTUP["zeitzone"])
except ZoneInfoNotFoundError:
    raise SystemExit(f"Zeitzone {STARTUP['zeitzone']!r} unbekannt oder Zeitzonendaten fehlen "
                     "(typisch unter Windows): `pip install tzdata`.") from None


def now_iso():
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_env():
    """Liest ROOT/.env, ohne bereits gesetzte Umgebungsvariablen zu überschreiben."""
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
META_API_VERSION = os.environ.get("META_API_VERSION") or "v26.0"
TOKEN_VORLAUF = 14  # Tage: so früh erinnert der Skill an die Erneuerung des Meta-Tokens


def token_erinnerung(startup, heute):
    """Erinnerung, den Meta-Token zu erneuern, oder None. Meta bietet für Systemnutzer-Token nur „nie“ oder 60 Tage;
    das Startup legt ihn ohne Ablauf an und erneuert ihn nach `meta_token.erneuern_nach_tagen` (startup.json)."""
    info = startup.get("meta_token") or {}
    if not info.get("erstellt"):
        return None
    faellig = date.fromisoformat(info["erstellt"]) + timedelta(days=info.get("erneuern_nach_tagen") or 180)
    rest = (faellig - heute).days
    if rest > TOKEN_VORLAUF:
        return None
    wann = f"seit {-rest} Tagen fällig" if rest < 0 else "heute fällig" if rest == 0 else f"in {rest} Tagen fällig"
    return f"Meta-Token erneuern, {wann} (ANLEITUNG.md, B6)."


# MEDIA_BUYING_MODUS=test: Testdaten aus <startup>/testdaten statt API, Bericht als TESTLAUF, keine Ausführung/Prüfung.
TEST_MODE = os.environ.get("MEDIA_BUYING_MODUS", "").strip().lower() == "test"
FIXTURE = STARTUP_DIR / "testdaten" / "testdaten.json"
TEST_OUT = STARTUP_DIR / "testdaten" / "testlaeufe"
# Ablage für Runden und Akten; im TEST-Modus getrennt vom echten Verlauf, mit denselben Unterordnern.
ABLAGE = TEST_OUT if TEST_MODE else STARTUP_DIR


def require_real_data():
    """Echte Läufe nur mit echten Startup-Daten; Beispielwerte der Vorlage erlauben nur den Testlauf."""
    if STARTUP.get("beispiel") and not TEST_MODE:
        raise SystemExit(f"{STARTUP_DIR.name}/startup.json enthält noch Beispielwerte (\"beispiel\": true). "
                         "Nur Testlauf möglich (MEDIA_BUYING_MODUS=test); für echte Läufe zuerst die Einrichtung "
                         "abschließen (references/einrichtung.md, Stand: einrichtung.py).")


def require_env(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"Fehlende Umgebungsvariablen: {', '.join(missing)} (siehe .env.example)")
    return [os.environ[n] for n in names]


class ApiError(Exception):
    pass


def _redact(text):
    for name in ("META_ACCESS_TOKEN", "TRIPLEWHALE_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            text = text.replace(secret, "***")
    return text


def http_json(method, url, params=None, body=None, headers=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:2000]
        raise ApiError(_redact(f"{method} {url.split('?')[0]} -> HTTP {e.code}: {detail}")) from None
    except urllib.error.URLError as e:
        raise ApiError(_redact(f"{method} {url.split('?')[0]} -> {e.reason}")) from None


def windows(run_day):
    """Standardfenster relativ zum Lauftag (Zeitzone des Startups): Vortag, 3 und 7 abgeschlossene Tage, heute (unvollständig)."""
    y = run_day - timedelta(days=1)
    return {
        "y": (y, y),
        "d3": (y - timedelta(days=2), y),
        "d7": (y - timedelta(days=6), y),
        "heute": (run_day, run_day),
    }


def parse_day(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


def runde(run_day):
    """Ordner einer Runde: Datenstände, Übersichten, Plan, Bericht, Verifikation."""
    return ABLAGE / "runden" / f"{run_day:%Y-%m-%d}"


def raw_dir(run_day):
    """Rohdaten des Lauftags (nicht versioniert)."""
    return runde(run_day) / "rohdaten"


def in_runden(muster):
    """Dateien aller Runden, z. B. alle Pläne; nach Dateiname sortiert (IDs tragen das Datum)."""
    return sorted((ABLAGE / "runden").glob(f"*/{muster}"), key=lambda p: p.name)


def datei(value):
    """Pfad oder bloßer Dateiname einer Runde (z. B. AUSFUEHRUNGSPLAN_20260115_BUDGET.json)."""
    p = Path(value)
    if p.exists():
        return p
    found = in_runden(p.name)
    if not found:
        raise SystemExit(f"{value} nicht gefunden (weder als Pfad noch in runden/<Datum>/).")
    return found[-1]


def akte(account_id, adset_id):
    """Akte je Adset. Im TEST-Modus getrennt von den echten Akten."""
    return ABLAGE / "akten" / f"meta_{account_id}_{adset_id}.md"


def write_text(path, text):
    """Schreibt UTF-8 mit LF-Zeilenenden, auch unter Windows (sonst sieht Git jede Datei als komplett geändert)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def write_json(path, data):
    return write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
