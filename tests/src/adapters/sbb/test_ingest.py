import unittest
from datetime import date, datetime

from src.adapters.sbb.ingest import (build_passenger_counts, build_platforms, build_stations,
                                     build_train_runs, build_waiting_halls, string)
from src.framex import Client
from src.runner import KB


def event(station, hour, *, day="2026-09-28", journey="journey", **extra):
    return dict(betriebstag=date.fromisoformat(day), fahrt_bezeichner=journey,
                bpuic=station, haltestellen_name=str(station), verkehrsmittel_text="IC",
                ankunftszeit=None, abfahrtszeit=datetime.fromisoformat(f"{day}T{hour}:00"),
                faellt_aus_tf=False, durchfahrt_tf=False, **extra)


class Ingestion(unittest.TestCase):
    def query_events(self, rows, stations):
        facts, _ = build_train_runs(rows, {station: {} for station in stations})
        c = Client()
        self.addCleanup(c.close)
        source = (KB / "ontology.fx").read_text() + (KB / "rules.fx").read_text()
        source += "\n".join(f"sp_{station}:StopPoint." for station in stations)
        c.load(source + "\n" + "\n".join(facts))
        return c, facts

    def test_cancellations_pass_throughs_and_foreign_stops(self):
        rows = [event(1, "08:00"), {**event(2, "08:05"), "faellt_aus_tf": True},
                {**event(3, "08:10"), "durchfahrt_tf": True}, event(4, "08:15"),
                event(99, "08:20"), event(5, "08:25")]
        c, _ = self.query_events(list(reversed(rows)), (1, 2, 3, 4, 5))
        self.assertEqual(c.query("?- sp_1[nonStopTo -> sp_4].")["status"], "true")
        for goal in ("sp_4[nonStopTo -> sp_5]", 'sp_2[servedByCategory -> "IC"]',
                     'sp_3[servedByCategory -> "IC"]'):
            self.assertEqual(c.query(f"?- {goal}.")["status"], "unknown")

    def test_same_journey_on_different_days_never_links(self):
        c, facts = self.query_events([event(1, "23:55"), event(2, "00:05", day="2026-09-29")], (1, 2))
        self.assertEqual(sum(":TrainRun." in fact for fact in facts), 2)
        self.assertEqual(c.query("?- sp_1[nonStopTo -> sp_2].")["status"], "unknown")

    def test_overnight_run_preserves_timestamp_order(self):
        first = event(1, "23:55")
        second = {**event(2, "00:05"), "abfahrtszeit": datetime(2026, 9, 29, 0, 5)}
        c, _ = self.query_events([second, first], (1, 2))
        self.assertEqual(c.query("?- sp_1[nonStopTo -> sp_2].")["status"], "true")

    def test_duplicates_and_input_order_do_not_change_event_identity(self):
        first, second = event(1, "08:00"), event(2, "08:05")
        scope = {1: {}, 2: {}}
        expected, _ = build_train_runs([first, second], scope)
        actual, _ = build_train_runs([second, first, first], scope)
        self.assertEqual(actual, expected)

    def test_missing_or_ambiguous_order_fails(self):
        for rows in ([{**event(1, "08:00"), "abfahrtszeit": None}],
                     [event(1, "08:00"), event(2, "08:00")]):
            with self.assertRaisesRegex(ValueError, "stop order"):
                build_train_runs(rows, {1: {}, 2: {}})

    def test_length_missing_and_passenger_conflicts_are_preserved(self):
        facts, notes = build_platforms([dict(fid=1, bpuic=1, p_nr="1/2", p_lange=None)], {1: {}})
        self.assertFalse(any("platformLength" in f for f in facts))
        self.assertIn("1 platforms have no length", str(notes))
        rows = [dict(uic=1, jahr_annee_anno="2024", dtv_tjm_tgm=n) for n in (10, 20)]
        facts, notes = build_passenger_counts(rows, {1: {}})
        self.assertEqual(len(facts), 2)
        self.assertIn("conflicting values: 1", str(notes))

    def test_waiting_hall_id_survives_status_change(self):
        row = dict(bpuic=1, linie=900, km=1.0, gebaudename="Hall", geopos=None, status="BESTEHEND")
        a, _ = build_waiting_halls([row], {1: {}})
        b, _ = build_waiting_halls([{**row, "status": "PROJEKTIERT ABBRUCH"}], {1: {}})
        self.assertEqual(a[0], b[0])
        with self.assertRaisesRegex(ValueError, "Conflicting statuses"):
            build_waiting_halls([row, {**row, "status": "PROJEKTIERT NEU"}], {1: {}})

    def test_string_escaping_round_trips_through_framex(self):
        label = 'Zürich "HB" \\ platform\nnext line'
        with Client() as c:
            c.load('world open. s[designation -> ' + string(label) + '].')
            self.assertEqual(c.query('?- s[designation -> ' + string(label) + '].')["status"], "true")

    def test_station_scope_and_same_name_distinct_ids(self):
        base = dict(isocountrycode="CH", stoppoint=True, meansoftransport="TRAIN",
                    designationofficial="Same name", cantonabbreviation=None, cantonname=None)
        rows = [{**base, "number": n} for n in (1, 2)]
        rows += [{**base, "number": 3, "isocountrycode": None},
                 {**base, "number": 4, "stoppoint": False},
                 {**base, "number": 5, "meansoftransport": "BUS"}]
        _, _, scope = build_stations(rows)
        self.assertEqual(set(scope), {1, 2})
