import unittest

from pydantic import ValidationError

from src.adapters.sbb.models import Platform, TrainEvent, WifiStation, validate_rows


class Models(unittest.TestCase):
    def test_identifiers_normalize_without_truncating(self):
        for value in (8507000, 8507000.0, "8507000", "8507000.0"):
            self.assertEqual(WifiStation(bpuic=value, standort="Bern").bpuic, 8507000)
        for value in (True, -1, "8507000.5", float("nan"), "bad"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                WifiStation(bpuic=value, standort="Bern")

    def test_missing_length_is_not_zero(self):
        row = dict(fid=1, bpuic="8507000", bps_name="Bern", p_nr="1/2", p_lange=None)
        self.assertIsNone(Platform.model_validate(row).p_lange)
        for bad in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValidationError):
                Platform.model_validate({**row, "p_lange": bad})

    def test_flags_are_parsed_and_missing_fields_fail_with_context(self):
        event = dict(betriebstag="2026-09-28", fahrt_bezeichner="run", bpuic=8507000,
                     haltestellen_name="Bern", verkehrsmittel_text="IC",
                     ankunftszeit=None, abfahrtszeit="2026-09-28T12:00:00",
                     faellt_aus_tf="false", durchfahrt_tf="true")
        parsed = TrainEvent.model_validate(event)
        self.assertFalse(parsed.faellt_aus_tf)
        self.assertTrue(parsed.durchfahrt_tf)
        del event["faellt_aus_tf"]
        with self.assertRaisesRegex(ValueError, "train_runs, row 1"):
            validate_rows("train_runs", [event])
