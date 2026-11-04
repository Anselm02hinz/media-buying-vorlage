"""Tests ohne Netzwerk: Kennzahlen aus Summen, Entscheidungsprüfung, Freigabe- und Schreibsperre.

    python -m unittest discover .agents/skills/media-buying/tests
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import abgleich  # noqa: E402
import akte  # noqa: E402
import build_dataset  # noqa: E402
import einrichtung  # noqa: E402
import plan as plan_cmd  # noqa: E402
import render_report  # noqa: E402
from common import ACCOUNTS, CURRENCY_SIGN, FIXTURE, read_json, windows  # noqa: E402


class AktenImTempordner(unittest.TestCase):
    """Akten landen während der Tests in einem Temp-Ordner, nie im Startup-Ordner."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        patcher = mock.patch.object(akte, "akte_path", lambda konto, adset: base / f"meta_{konto}_{adset}.md")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.akte_datei = lambda konto, adset: base / f"meta_{konto}_{adset}.md"

# Tests laufen mit jeder startup.json: erstes Konto, dessen Präfix und Währungszeichen.
KONTO = next(iter(ACCOUNTS))
PREFIX = ACCOUNTS[KONTO]["prefix"]
S = CURRENCY_SIGN


class Kennzahlen(unittest.TestCase):
    daily = {
        "2026-10-18": {"spend": 100.0, "purchases": 2, "revenue": 300.0, "link_clicks": 50},
        "2026-10-19": {"spend": 50.0, "purchases": 0, "revenue": 0.0, "link_clicks": 0},
        "2026-10-20": {"spend": 0.0, "purchases": 0, "revenue": 0.0, "link_clicks": 0},
    }

    def test_aus_summen_nicht_tagesmittel(self):
        m = build_dataset.aggregate(self.daily, date(2026, 10, 18), date(2026, 10, 20))
        self.assertEqual(m["roas"], 2.0)          # 300/150, nicht Mittel aus 3,0 und 0
        self.assertEqual(m["cpa"], 75.0)
        self.assertEqual(m["link_cpc"], 3.0)      # 150/50

    def test_nullnenner_nicht_berechenbar(self):
        m = build_dataset.aggregate(self.daily, date(2026, 10, 20), date(2026, 10, 20))
        self.assertIsNone(m["roas"])
        self.assertIsNone(m["cpa"])
        self.assertIsNone(m["link_cpc"])

    def test_kaeufe_omni_vor_pixel(self):
        actions = [{"action_type": "offsite_conversion.fb_pixel_purchase", "value": "1"},
                   {"action_type": "omni_purchase", "value": "3"}]
        self.assertEqual(build_dataset.action_value(actions), 3.0)

    def test_fenster(self):
        w = windows(date(2026, 10, 22))
        self.assertEqual(w["y"], (date(2026, 10, 21), date(2026, 10, 21)))
        self.assertEqual(w["d7"][0], date(2026, 10, 15))

    def test_zeitformate(self):
        a = build_dataset.parse_time("2026-10-19T01:50:21+0000")
        b = build_dataset.parse_time("2026-10-19T03:50:21.815255+02:00")
        self.assertEqual(a.replace(microsecond=0), b.replace(microsecond=0))


def dataset(*rows):
    return {"rows": [dict({"konto": KONTO, "account_id": "1", "campaign_id": "c", "budget_ebene": "adset",
                           "effective_status": "ACTIVE", "status": "ACTIVE"}, **r) for r in rows]}


class Entscheidungen(unittest.TestCase):
    def test_unter_mindestbudget_aktiv_wird_abgelehnt(self):
        ds = dataset({"id": "a", "name": "A", "budget": render_report.MIN_BUDGET + 10})
        with self.assertRaises(SystemExit):
            render_report.build_rows(ds, {"entscheidungen": [
                {"id": "a", "ziel_budget": render_report.MIN_BUDGET - 1, "grund": "x"}]})

    def test_aktives_adset_ohne_entscheidung(self):
        ds = dataset({"id": "a", "name": "A", "budget": 33.0}, {"id": "b", "name": "B", "budget": 44.0})
        with self.assertRaises(SystemExit):
            render_report.build_rows(ds, {"entscheidungen": [{"id": "a", "ziel_budget": 33, "grund": "x"}]})

    def test_entscheidungsart(self):
        ds = dataset({"id": "a", "name": "A", "budget": 88.0}, {"id": "b", "name": "B", "budget": 44.0})
        rows = render_report.build_rows(ds, {"entscheidungen": [
            {"id": "a", "ziel_budget": 44, "grund": "x"},
            {"id": "b", "ziel_status": "PAUSED", "grund": "y"}]})
        self.assertEqual([r["decision"] for r in rows], ["SENKEN", "PAUSIEREN"])
        self.assertEqual(rows[0]["code"], f"{PREFIX}01")


class PhaseUndSeparat(unittest.TestCase):
    def test_vorher_nachher_aus_meta_aktivitaet(self):
        nested = '{"old_value": {"type": "daily_budget", "old_value": 8800}, "new_value": {"new_value": 4400}}'
        self.assertEqual(build_dataset.change_values("update_ad_set_budget", nested), (88.0, 44.0))
        self.assertEqual(build_dataset.change_values("update_ad_set_budget", '{"old_value": 3300, "new_value": "6600"}'),
                         (33.0, 66.0))
        self.assertEqual(build_dataset.change_values("update_ad_set_budget", "kein json"), (None, None))

    def test_phase_aus_datenstand(self):
        row = {"letzte_aenderung": {"zeit": "2026-10-25T03:00+01:00", "quelle": "x", "art": "budget",
                                    "vorher": 88.0, "nachher": 44.0},
               "erster_liefertag": "2026-10-20", "liefert_schon_vor_zeitraum": False}
        self.assertEqual(build_dataset.phase_text(row),
                         f"Seit 25.10. 03:00 Uhr: 88 {S} → 44 {S}. Erster Liefertag 20.10.")
        self.assertIn("ohne bekannte Werte", build_dataset.phase_text(
            {"letzte_aenderung": {"zeit": "2026-10-25T03:00+01:00", "quelle": "Meta", "vorher": None}}))
        self.assertIn("Keine Budget- oder Statusänderung", build_dataset.phase_text({}))

    def test_separate_adsets_nicht_im_plan(self):
        ds = dataset({"id": "a", "name": "A", "budget": 88.0},
                     {"id": "s", "name": "Follower", "budget": 5.0, "separat": "Follower"})
        rows = render_report.build_rows(ds, {"entscheidungen": [{"id": "a", "ziel_budget": 88, "grund": "x"}]})
        self.assertEqual([r["id"] for r in rows], ["a"])  # keine Entscheidung für s nötig
        with self.assertRaises(SystemExit):  # und auch keine erlaubt
            render_report.build_rows(ds, {"entscheidungen": [{"id": "a", "ziel_budget": 88, "grund": "x"},
                                                            {"id": "s", "ziel_budget": 5, "grund": "y"}]})
        self.assertEqual(render_report.separate_budgets(ds, KONTO), {"s": ("Follower", 5.0)})

    def test_uebersicht_abschnitte_und_kontrolle(self):
        ds = dataset({"id": "a", "name": "A | Test", "budget": 88.0, "phase": "Seit 25.10.: 88 → 44.",
                      "meta": {"y": {"roas": 1.5, "kaeufe": 2.0, "spend": 60.0, "link_cpc": 1.1}}, "tw": None,
                      "meta_taeglich": {"2026-10-25": {"spend": 60.0, "purchases": 2.0, "revenue": 90.0}},
                      "aenderungen": [{"zeit": "2026-10-25T03:00+01:00", "art": "budget", "vorher": 88.0,
                                       "nachher": 44.0, "wer": "Max Muster", "bewertung": "abweichend"}],
                      "akte": ["25.10.2026 · Entscheidung · korrigiert, Grund: Testgrund"],
                      "hinweise": ["gestern erster vollständiger Liefertag"]},
                     {"id": "s", "name": "Follower", "budget": 5.0, "separat": "Follower", "meta": {}, "tw": None},
                     {"id": "p", "name": "Pausiert heute", "budget": 33.0, "effective_status": "PAUSED",
                      "status": "PAUSED", "phase": "Seit 26.10.: AN → AUS.", "meta": {}, "tw": None, "bewegung": True},
                     {"id": "r", "name": "Ruhend", "budget": 33.0, "effective_status": "PAUSED", "status": "PAUSED",
                      "phase": "", "meta": {}, "tw": None})
        ds.update({"id": "D-1", "test": False, "lauftag": "2026-10-26", "luecken": [], "kontrolle": {"aktiv_meta": 2},
                   "offene_fragen": [{"id": "a", "konto": KONTO, "name": "A", "zeit": "2026-10-25T03:00+01:00",
                                      "art": "budget", "vorher": 88.0, "nachher": 44.0, "wer": "Max Muster",
                                      "bewertung": "ohne Plan", "text": "Budget 88 → 44 durch Max."}],
                   "fenster": {"y": ["2026-10-25"] * 2, "d3": ["2026-10-23", "2026-10-25"],
                               "d7": ["2026-10-19", "2026-10-25"]}})
        text = build_dataset.overview(ds)
        self.assertIn("2 aktive Adsets laut Meta = 1 zu entscheiden (A) + 1 mit Kampagnenbudget oder separat (C).", text)
        self.assertNotIn("ABWEICHUNG – Datenstand", text)
        self.assertIn("**A | Test** · `a` · 88", text)
        self.assertIn("- Tage: 25. 60/2/1.50", text)
        self.assertIn("25.10. 88→44 Max ABWEICHEND", text)
        self.assertIn("- Akte: 25.10.2026 · Entscheidung · korrigiert, Grund: Testgrund", text)
        self.assertIn("## B · ", text)
        self.assertIn("Pausiert heute", text)
        self.assertIn("separat laut startup.json: Follower", text)
        self.assertIn("## D · Ruhend · 1", text)
        self.assertIn("Offene Fragen an", text)

    def test_ereignisse_mit_person_ohne_veroeffentlichung(self):
        raw = {"k": {"activities": [
            {"event_type": "create_ad_set", "object_id": "1", "event_time": "2026-10-26T03:00:00+0000",
             "extra_data": '{"old_value": null, "new_value": 8800}', "actor_name": "Max Muster"},
            {"event_type": "update_ad_set_run_status", "object_id": "1", "event_time": "2026-10-26T03:01:00+0000",
             "extra_data": '{"old_value": "Prozess „Ausstehend“", "new_value": "Aktiv"}'},
            {"event_type": "update_ad_set_budget", "object_id": "1", "event_time": "2026-10-27T02:00:00+0000",
             "extra_data": '{"old_value": 8800, "new_value": 4400}', "actor_name": "Max Muster",
             "application_name": "Power Editor"}]}}
        evs = build_dataset.ereignisse(raw)
        self.assertEqual([(e["art"], e["vorher"], e["nachher"]) for e in evs],
                         [("neu", None, 88.0), ("budget", 88.0, 44.0)])
        self.assertEqual(evs[1]["werkzeug"], "Power Editor")

    def test_hinweis_budget_passt_nicht_zum_verlauf(self):
        row = {"effective_status": "ACTIVE", "budget_ebene": "adset", "budget": 100.0,
               "updated_time": "2026-10-27T01:09:00+0000", "meta": {}, "meta_taeglich": {"2026-10-27": {"spend": 5}}}
        evs = [{"art": "budget", "zeit": "2026-10-26T03:00+01:00", "vorher": 88.0, "nachher": 44.0}]
        out = build_dataset.hinweise(row, date(2026, 10, 28), windows(date(2026, 10, 28)), evs)
        self.assertTrue(any("passt nicht zum letzten Verlaufswert 44" in h for h in out))


class Bericht(unittest.TestCase):
    def test_korrektur_ueber_plan_und_rendern(self):
        ds = dataset({"id": "a", "name": "Langer Name A", "budget": 88.0, "erster_liefertag": "2026-10-15",
                      "meta": {}, "tw": None},
                     {"id": "b", "name": "B", "budget": 44.0, "meta": {}, "tw": None})
        ds.update({"lauftag": "2026-10-22", "id": "D-1", "erstellt": "2026-10-22T03:00:00+02:00", "luecken": [],
                   "fenster": {"y": ["2026-10-21", "2026-10-21"], "d3": ["2026-10-19", "2026-10-21"],
                               "d7": ["2026-10-15", "2026-10-21"], "heute": ["2026-10-22", "2026-10-22"]},
                   "meta": {"api_version": "v26.0", "kauf_action_type": "omni_purchase"}, "konten": {}})
        rows = render_report.build_rows(ds, {"entscheidungen": [
            {"id": "a", "ziel_budget": 44, "grund": "x", "kurzname": "A"},
            {"id": "b", "ziel_budget": 44, "grund": "y"}]})
        plan = {"report_id": "R-1", "change_id": "A-1", "approval": {"status": "OFFEN"}, "rows": rows,
                "bericht": {"kopf": "Test"}}
        row_a = next(r for r in plan["rows"] if r["id"] == "a")
        row_a["target_budget"] = 66  # Korrektur des Entscheiders
        again = {r["id"]: r for r in render_report.build_rows(ds, render_report.decisions_from_plan(plan))}
        self.assertEqual(again["a"]["decision"], "SENKEN")
        self.assertEqual(again["a"]["kurzname"], "A")
        page = render_report.render(ds, plan, plan["bericht"])
        self.assertIn(f"88 {S} → 66 {S}", page)
        self.assertIn("Freigabe offen", page)
        self.assertEqual(again["a"]["vorschlag"], {"budget": 44, "status": "ACTIVE", "grund": "x"})  # bleibt erhalten

    def test_chat_kurz_mit_korrekturen(self):
        ds = dataset(*({"id": str(i), "name": f"S{i}", "budget": 88.0} for i in range(8)))
        rows = render_report.build_rows(ds, {"entscheidungen": [
            {"id": str(i), "ziel_budget": 44, "grund": "x"} for i in range(8)]})
        rows[0]["target_budget"] = 66  # Korrektur des Entscheiders
        plan = {"rows": rows}
        out = render_report.ROOT / "tests" / "R-x.html"
        text = render_report.chat_summary({"rows": []}, plan, out)
        self.assertIn(f"Vorschlag 44 {S} → jetzt 66 {S}", text)
        self.assertEqual(text.count(f"88 {S} → 44 {S}"), render_report.TOP_CASES)  # nicht alle 8 Zeilen
        self.assertIn("Alle 8 Änderungen", text)

    def test_angewendete_learnings_gezaehlt(self):
        rows = [{"rules": ["MB-0004 v1", "L-03"]}, {"rules": ["L-03", "L-01"]}, {"rules": ["MB-0002 v1"]}]
        self.assertEqual(render_report.learnings_text(rows), "Angewendete Learnings: L-01 ×1 · L-03 ×2")
        self.assertEqual(render_report.learnings_text([{"rules": ["MB-0001 v1"]}]), "")

    def test_zielwerte_gesamt_oder_je_produkt(self):
        with mock.patch.dict(render_report.STARTUP, {"zielwerte": {"ziel_roas": 2.0,
                                                                   "break_even": {"A": 1.6, "B": None}}}):
            self.assertEqual(render_report.targets_text(), "Meta-Ziel 2,00; Break-even A 1,60, B offen.")
        with mock.patch.dict(render_report.STARTUP, {"zielwerte": {"ziel_roas": {"A": 2.2, "B": None},
                                                                   "break_even": {"A": 1.6, "B": 1.8}}}):
            self.assertEqual(render_report.targets_text(), "Meta-Ziel A 2,20, B offen; Break-even A 1,60, B 1,80.")
        with mock.patch.dict(render_report.STARTUP, {"zielwerte": {"ziel_roas": None, "break_even": {}}}):
            self.assertEqual(render_report.targets_text(), "Meta-Ziel offen; Break-even offen.")


class Testmodus(unittest.TestCase):
    def test_testdaten_im_api_format(self):
        import fetch_meta
        key, spec = next(iter(read_json(FIXTURE)["konten"].items()))
        raw = fetch_meta.test_account(key, date(2026, 10, 22), 14)
        self.assertTrue(raw["testdaten"])
        self.assertEqual(len(raw["adsets"]), len(spec["adsets"]))
        days = {r["date_start"] for r in raw["insights"]}
        self.assertEqual(max(days), "2026-10-21")  # gestern relativ zum Lauftag
        daily = build_dataset.meta_daily(raw["insights"])
        self.assertTrue(all(isinstance(v["spend"], float) for d in daily.values() for v in d.values()))

    def test_dateiname_oder_pfad(self):
        import common
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(common, "ABLAGE", Path(tmp)):
            found = common.runde(date(2026, 10, 28)) / "D-1.json"
            found.parent.mkdir(parents=True)
            found.write_text("{}", encoding="utf-8")
            self.assertEqual(common.datei("D-1.json"), found)
            self.assertEqual(common.datei("startup/runden/2026-10-28/D-1.json"), found)
            self.assertEqual(common.datei(__file__), Path(__file__))
            with self.assertRaises(SystemExit):
                common.datei("D-2.json")

    def test_testplan_sperrt_ausfuehrung_und_pruefung(self):
        with self.assertRaises(SystemExit):
            plan_cmd.refuse_test({"test": True}, "Prüfung")


class Freigabe(AktenImTempordner):
    def plan(self):
        return {"change_id": "A-1", "report_id": "R-1", "status": "VORGESCHLAGEN", "approval": {"status": "OFFEN"},
                "rows": [{"id": "a", "code": "A01", "account_id": "1", "name": "A", "budget": 88.0,
                          "status": "ACTIVE", "target_budget": 44, "target_status": "ACTIVE", "decision": "SENKEN",
                          "reason": "Grund Skill", "vorschlag": {"budget": 44, "status": "ACTIVE",
                                                                 "grund": "Grund Skill"}}]}

    def test_korrektur_behaelt_vorschlag_und_landet_in_akte(self):
        p = self.plan()
        plan_cmd.cmd_korrigieren(p, SimpleNamespace(id="A01", budget=66.0, status=None, grund="Testgrund", von=None))
        row = p["rows"][0]
        self.assertEqual((row["target_budget"], row["decision"]), (66.0, "SENKEN"))
        self.assertEqual(row["reason"], "Grund Skill")
        self.assertEqual(row["vorschlag"]["grund"], "Grund Skill")
        self.assertEqual(row["entscheidung"]["art"], "korrigiert")
        plan_cmd.cmd_freigeben(p, SimpleNamespace(von="Entscheider", wortlaut="Go mit Korrektur"))
        text = self.akte_datei("1", "a").read_text(encoding="utf-8")
        self.assertIn("korrigiert** – Vorschlag Skill 44", text)
        self.assertIn("Grund: Testgrund", text)
        with self.assertRaises(SystemExit):  # nach Freigabe keine Korrektur mehr
            plan_cmd.cmd_korrigieren(p, SimpleNamespace(id="a", budget=88.0, status=None, grund=None, von=None))

    def test_korrektur_unter_mindestbudget_verweigert(self):
        with self.assertRaises(SystemExit):
            plan_cmd.cmd_korrigieren(self.plan(), SimpleNamespace(id="a", budget=render_report.MIN_BUDGET - 1,
                                                                  status=None, grund=None, von=None))

    def test_freigabe_ohne_korrektur_heisst_uebernommen(self):
        p = self.plan()
        plan_cmd.cmd_freigeben(p, SimpleNamespace(von="Entscheider", wortlaut="Go"))
        self.assertEqual(p["rows"][0]["entscheidung"]["art"], "übernommen")
        self.assertIn("Vorschlag übernommen", self.akte_datei("1", "a").read_text(encoding="utf-8"))

    def test_ausfuehren_ohne_freigabe_verweigert(self):
        with self.assertRaises(SystemExit):
            plan_cmd.cmd_ausfuehren(self.plan(), "token", "v26.0")

    def test_ausfuehren_ohne_schreibschalter_verweigert(self):
        p = self.plan()
        plan_cmd.cmd_freigeben(p, SimpleNamespace(von="Entscheider", wortlaut="Go, alles wie vorgeschlagen"))
        os.environ.pop("META_WRITE_ENABLED", None)
        with self.assertRaises(SystemExit):
            plan_cmd.cmd_ausfuehren(p, "token", "v26.0")

    def test_freigabe_braucht_wortlaut(self):
        with self.assertRaises(SystemExit):
            plan_cmd.cmd_freigeben(self.plan(), SimpleNamespace(von="Entscheider", wortlaut="  "))


class Akte(AktenImTempordner):
    def test_einmal_schreiben_neuester_oben(self):
        e1 = akte.eintrag("2026-10-27T03:00+01:00", "Änderung laut Meta", "meta", "k1", "88 → 44")
        e2 = akte.eintrag("2026-10-28T11:00+01:00", "Vorschlag · A-1", "vorschlag", "A-1", "Grund: schwach")
        self.assertTrue(akte.schreiben("1", "a", "A", e1, "meta", "k1"))
        self.assertFalse(akte.schreiben("1", "a", "A", e1, "meta", "k1"))  # keine Doppelung
        akte.schreiben("1", "a", "A", e2, "vorschlag", "A-1")
        text = self.akte_datei("1", "a").read_text(encoding="utf-8")
        self.assertLess(text.index("Vorschlag · A-1"), text.index("Änderung laut Meta"))
        self.assertTrue(text.rstrip().endswith("Konto 1 · Adset a"))

    def test_offener_vorschlag_wird_ersetzt(self):
        akte.schreiben("1", "a", "A", akte.eintrag("2026-10-28T11:00+01:00", "Vorschlag · A-1", "vorschlag", "A-1",
                                                   "alt"), "vorschlag", "A-1")
        akte.schreiben("1", "a", "A", akte.eintrag("2026-10-28T11:00+01:00", "Vorschlag · A-1", "vorschlag", "A-1",
                                                   "neu"), "vorschlag", "A-1", replace=True)
        text = self.akte_datei("1", "a").read_text(encoding="utf-8")
        self.assertIn("neu", text)
        self.assertNotIn("alt", text)
        self.assertEqual(text.count("Vorschlag · A-1"), 1)

    def test_auszug_nur_begruendungen(self):
        akte.schreiben("1", "a", "A", akte.eintrag("2026-10-27T03:00+01:00", "Vorschlag · A-0", "vorschlag", "A-0",
                                                   "Grund: [Bericht](x.html) stark"), "vorschlag", "A-0")
        akte.schreiben("1", "a", "A", akte.eintrag("2026-10-28T03:00+01:00", "Änderung laut Meta", "meta", "k",
                                                   "88 → 44"), "meta", "k")
        out = akte.auszug("1", "a")
        self.assertEqual(len(out), 1)
        self.assertIn("Grund: Bericht stark", out[0])

    def test_letzter_grund(self):
        at = "2026-10-28T12:00:00+01:00"
        akte.schreiben("1", "a", "A", akte.eintrag(at, "Grund von Media Buyer", "grund", f"a@{at}", "Testgrund"),
                       "grund", f"a@{at}")
        self.assertEqual(akte.letzter_grund("1", "a"), at)


class Abgleich(unittest.TestCase):
    plan = (datetime.fromisoformat("2026-10-28T02:00:00+01:00"), "p.json",
            {"change_id": "A-1", "rows": [{"id": "a", "target_status": "ACTIVE", "target_budget": 44.0,
                                           "vorschlag": {"status": "ACTIVE", "budget": 33.0}}]})

    def ev(self, **kw):
        return {"id": "a", "zeit": "2026-10-28T09:00+01:00", "art": "budget", "vorher": 88.0, "nachher": 44.0, **kw}

    def test_bewertung(self):
        self.assertEqual(abgleich.bewerten(self.ev(), [self.plan])[0], "wie entschieden")
        self.assertEqual(abgleich.bewerten(self.ev(nachher=133.0), [self.plan])[0], "abweichend")
        self.assertEqual(abgleich.bewerten(self.ev(art="status", vorher="Aktiv", nachher="Inaktiv"), [self.plan])[0],
                         "abweichend")
        self.assertEqual(abgleich.bewerten(self.ev(id="b"), [self.plan])[0], "ohne Plan")
        self.assertEqual(abgleich.bewerten(self.ev(zeit="2026-10-30T09:00+01:00"), [self.plan])[0], "ohne Plan")

    def test_satz_nennt_vorschlag_und_entscheidung(self):
        b, p, r = abgleich.bewerten(self.ev(nachher=133.0, wer="Max Muster", werkzeug="Power Editor"), [self.plan])
        text = abgleich.satz(self.ev(nachher=133.0, wer="Max Muster", werkzeug="Power Editor"), b, p, r)
        self.assertIn("durch Max Muster (Power Editor)", text)
        self.assertIn(f"entschieden 44 {S}, Vorschlag Skill 33 {S}", text)
        self.assertIn("Grund nicht genannt", text)


if __name__ == "__main__":
    unittest.main()


class LueckenImMetaVerlauf(unittest.TestCase):
    """Meta liefert den Änderungsverlauf unvollständig: zwei Abrufwege, dazu Ableitung aus dem letzten
    eigenen Datenstand."""

    def test_abrufwege_werden_ohne_doppelungen_zusammengefuehrt(self):
        import fetch_meta
        ev = lambda t: {"event_time": t, "event_type": "update_ad_set_budget", "object_id": "a"}  # noqa: E731
        erster_tag = int(datetime(2026, 10, 26, tzinfo=fetch_meta.TZ).timestamp())

        def graph(path, token, version, **params):
            if "until" not in params:
                return [ev("t1"), ev("t2")]
            return [ev("t2"), ev("t3")] if params["since"] == erster_tag else []

        with mock.patch.object(fetch_meta, "graph", graph):
            out, zahlen = fetch_meta.activities("act_1", date(2026, 10, 26), date(2026, 10, 28), "x", "v")
        self.assertEqual(sorted(a["event_time"] for a in out), ["t1", "t2", "t3"])
        self.assertEqual(zahlen, {"am_stueck": 2, "tageweise": 2, "zusammen": 3})

    def test_fehlende_wechsel_aus_letztem_datenstand(self):
        prev = {"id": "D-1", "erstellt": "2026-10-28T12:00:00+01:00", "rows": [
            {"id": "a", "budget_ebene": "adset", "budget": 88.0, "status": "ACTIVE"},
            {"id": "b", "budget_ebene": "adset", "budget": 33.0, "status": "ACTIVE"},
            {"id": "c", "budget_ebene": "adset", "budget": 44.0, "status": "ACTIVE"}]}
        raw = {"k": {"adsets": [
            {"id": "a", "status": "ACTIVE", "daily_budget": "4400", "updated_time": "2026-10-30T03:45:00+0100"},
            {"id": "b", "status": "PAUSED", "daily_budget": "3300"},
            {"id": "c", "status": "ACTIVE", "daily_budget": "8800"}],
            "activities": [{"event_time": "2026-10-29T03:00:00+0100", "event_type": "update_ad_set_budget",
                            "object_id": "c", "extra_data": '{"old_value": 4400, "new_value": 8800}'}]}}
        self.assertEqual(build_dataset.aus_datenstand(raw, prev), 2)  # a: Budget, b: Status; c steht im Verlauf
        last = build_dataset.last_changes(raw)
        self.assertEqual((last["a"]["vorher"], last["a"]["nachher"]), (88.0, 44.0))
        self.assertTrue(last["a"]["zeit"].startswith("2026-10-30T03:45"))
        self.assertIn("abgeleitet aus D-1", last["a"]["quelle"])
        self.assertEqual((last["b"]["art"], last["b"]["nachher"]), ("status", "Inaktiv"))
        self.assertEqual(build_dataset.aus_datenstand(raw, None), 0)

    def test_drosselung_wird_einmal_abgewartet(self):
        import fetch_meta
        antworten = [fetch_meta.ApiError('GET x -> HTTP 400: {"error":{"code":17,"error_subcode":2446079}}'),
                     {"data": [{"id": "a"}]}]

        def http_json(method, url, params=None):
            a = antworten.pop(0)
            if isinstance(a, Exception):
                raise a
            return a

        with mock.patch.object(fetch_meta, "http_json", http_json), mock.patch.object(fetch_meta.time, "sleep") as s:
            self.assertEqual(fetch_meta.graph("act_1/adsets", "x", "v"), [{"id": "a"}])
        s.assert_called_once_with(fetch_meta.WARTEN)


class StartupOrdner(unittest.TestCase):
    """Der Kern findet den Startup-Ordner an seiner startup.json, egal wie er heißt."""

    def test_einziger_ordner_mit_startup_json(self):
        import common
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".agents").mkdir()
            with self.assertRaises(SystemExit):
                common.find_startup(root)  # keiner
            (root / "acme").mkdir()
            (root / "acme" / "startup.json").write_text("{}", encoding="utf-8")
            self.assertEqual(common.find_startup(root), root / "acme")
            (root / "zweiter").mkdir()
            (root / "zweiter" / "startup.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(SystemExit):
                common.find_startup(root)  # mehrere


class Einrichtung(unittest.TestCase):
    """Prüfskript der Einrichtung: erkennt Platzhalter und Lücken, nennt den nächsten Schritt, zeigt nie Zugangsdaten."""

    def test_platzhalter_der_vorlage(self):
        vorlage = {"beispiel": True, "name": "Beispiel-Startup", "entscheider": "Vorname Nachname",
                   "systemverantwortlich": "Vorname Nachname", "mindestbudget": 20, "mindestbudget_regel": "OFFEN",
                   "zielwerte": {"ziel_roas": None, "break_even": {"Produkt A": None}},
                   "konten": {"haupt": {"id": "100000000000001", "prefix": "A"}}, "triple_whale": {"aktiv": False}}
        out = einrichtung.pruefe_stammdaten(vorlage, "startup")
        self.assertEqual({b["schritt"] for b in out if b["status"] == "FEHLT"}, {"angaben", "konten", "bestaetigung"})
        self.assertTrue(any(b["status"] == "OFFEN" and "Ziel-ROAS" in b["text"] for b in out))
        self.assertTrue(any(b["status"] == "HINWEIS" and "umbenennen" in b["text"] for b in out))

    def test_ziel_roas_je_produkt(self):
        texte = lambda out, status: [b["text"] for b in out if b["status"] == status]  # noqa: E731
        out = einrichtung.pruefe_zielwerte({"ziel_roas": {"Serum": 2.2, "Creme": None},
                                            "break_even": {"Serum": 1.6, "Creme": 1.8, "Set": 2.0}})
        self.assertEqual(texte(out, "OFFEN"), ["Ziel-ROAS Creme: OFFEN", "Ziel-ROAS Set: OFFEN"])
        self.assertEqual(texte(out, "FEHLT") + texte(out, "HINWEIS"), [])
        out = einrichtung.pruefe_zielwerte({"ziel_roas": 2.0, "break_even": {"Serum": 1.6, "Creme": 2.5}})
        self.assertEqual(texte(out, "HINWEIS"), ["Creme: Ziel-ROAS 2 liegt unter Break-even 2.5; "
                                                 "ggf. Ziel-ROAS je Produkt festlegen"])
        out = einrichtung.pruefe_zielwerte({"ziel_roas": {"Serum": "2,2", "Produkt A": None},
                                            "break_even": {"Serum": 1.6}})
        self.assertEqual(texte(out, "FEHLT"), ["Ziel-ROAS: Produkte sind noch Beispielwerte",
                                               "Ziel-ROAS Serum: '2,2' ist keine Zahl"])

    def test_testdaten_ohne_konto(self):
        out = einrichtung.pruefe_testdaten({KONTO: {}, "zweitkonto": {}}, FIXTURE)
        self.assertEqual(out[0]["status"], "FEHLT")
        self.assertIn("zweitkonto", out[0]["text"])

    def test_kontovergleich(self):
        gesehen = [{"account_id": "1", "currency": "USD", "timezone_name": "Europe/Berlin", "account_status": 1}]
        out = einrichtung.vergleiche_konten({"a": {"id": "1"}, "b": {"id": "2"}}, gesehen, "Europe/Berlin", "EUR")
        self.assertEqual([(b["status"], b["schritt"]) for b in out], [("FEHLT", "angaben"), ("FEHLT", "konten")])
        self.assertIn("Währung USD", out[0]["text"])

    def test_vorschlag_separat(self):
        camps = [{"name": "Verkauf", "objective": "OUTCOME_SALES"}, {"name": "Follower", "objective": "OUTCOME_ENGAGEMENT"}]
        self.assertEqual([c["name"] for c in einrichtung.vorschlag_separat(camps)], ["Follower"])

    def test_naechster_schritt(self):
        b = einrichtung.befund
        nr, name, _ = einrichtung.naechster_schritt([b("FEHLT", "konten", "x"), b("FEHLT", "internet", "y"),
                                                     b("OK", "meta", "z")])
        self.assertEqual((nr, name), (3, "Internetzugang"))
        self.assertIsNone(einrichtung.naechster_schritt([b("OK", "meta", "z"), b("OFFEN", "angaben", "o")])[0])

    def test_netzfehler_heisst_internetzugang(self):
        def offline(*args, **kwargs):
            raise einrichtung.ApiError("GET https://graph.facebook.com/v26.0/me/adaccounts -> Temporary failure")

        def token_abgelaufen(*args, **kwargs):
            raise einrichtung.ApiError('GET x -> HTTP 400: {"error":{"message":"expired","code":190}}')

        with mock.patch.object(einrichtung, "graph", offline):
            out, konten = einrichtung.pruefe_meta("x", "v")
        self.assertIsNone(konten)
        self.assertEqual((out[0]["status"], out[0]["schritt"]), ("FEHLT", "internet"))
        with mock.patch.object(einrichtung, "graph", token_abgelaufen):
            out, _ = einrichtung.pruefe_meta("x", "v")
        self.assertEqual(out[0]["schritt"], "meta")  # Meta-Fehler mit JSON-Antwort ist kein Netzproblem
        self.assertIn("abgelaufen", out[0]["text"])

    def test_token_nie_in_der_ausgabe(self):
        geheim = "EAAgeheim123"
        konten = [{"account_id": "1", "name": "K", "currency": "EUR", "timezone_name": "Europe/Berlin",
                   "account_status": 1}]

        def graph(path, token, version, **params):
            return [{"permission": "ads_read", "status": "granted"}] if path == "me/permissions" else konten

        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"META_ACCESS_TOKEN": geheim, "META_WRITE_ENABLED": "1"}), \
                mock.patch.object(einrichtung, "graph", graph), mock.patch.object(einrichtung, "TEST_MODE", False), \
                mock.patch.object(sys, "argv", ["einrichtung.py"]), contextlib.redirect_stdout(buf):
            einrichtung.main()
        text = buf.getvalue()
        self.assertNotIn(geheim, text)
        self.assertIn("META_ACCESS_TOKEN gesetzt", text)
        self.assertIn("Schreibzugriff ist eingeschaltet", text)
        self.assertIn("Nächster Schritt:", text)

    def test_regeln_noetig_formatbeispiel_zaehlt_nicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "MEDIA_BUYING_REGELN.md"
            path.write_text("# Regeln\n\n```markdown\n## MB-0001 · v1 · <Titel>\n```\n", encoding="utf-8")
            self.assertEqual(einrichtung.pruefe_regeln(path)[0]["status"], "FEHLT")
            path.write_text(path.read_text(encoding="utf-8") + "\n## MB-0001 · v1 · Erhöhen\n\n## MB-0002 · v1 · Senken\n",
                            encoding="utf-8")
            out = einrichtung.pruefe_regeln(path)
        self.assertEqual((out[0]["status"], out[0]["text"]), ("OK", "2 Media-Buying-Regeln festgelegt"))

    def test_token_erinnerung(self):
        from common import token_erinnerung
        startup = {"meta_token": {"erstellt": "2026-01-01", "erneuern_nach_tagen": 180}}  # fällig am 30.06.
        self.assertIsNone(token_erinnerung(startup, date(2026, 6, 1)))
        self.assertIn("in 10 Tagen fällig", token_erinnerung(startup, date(2026, 6, 20)))
        self.assertIn("seit 2 Tagen fällig", token_erinnerung(startup, date(2026, 7, 2)))
        self.assertIsNone(token_erinnerung({"meta_token": {"erstellt": None}}, date(2026, 7, 2)))
        self.assertEqual(einrichtung.pruefe_token({}, date(2026, 7, 2), True)[0]["status"], "OFFEN")
