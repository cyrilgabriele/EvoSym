"""Sample tests always run; RUN_SBB_TESTS=1 also verifies the local SBB snapshot."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from src.framex import Client
from src.queries import QUESTIONS
from src.runner import ROOT, inputs, load_client, schema_failures


def value(raw):
    if raw.startswith("sp_"):
        return int(raw.removeprefix("sp_"))
    if raw.startswith('"'):
        return json.loads(raw)
    try:
        return float(raw)
    except ValueError:
        return raw


class SampleQuestions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client, _ = load_client()
        cls.expected = json.loads(Path(__file__).with_name("sample_expected.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_all_18_answers(self):
        self.assertEqual(len(QUESTIONS), 18)
        self.assertEqual({q.id for q in QUESTIONS}, set(self.expected))
        for question in QUESTIONS:
            with self.subTest(question=question.id):
                result = self.client.query(question.query)
                expected = self.expected[question.id]
                if isinstance(expected, str):
                    self.assertEqual(result["status"], expected)
                else:
                    self.assertEqual(result["status"], "bindings")
                    self.assertCountEqual(result["bindings"], expected)

    def test_thresholds_and_missing_evidence(self):
        for goal in (
            "platform_bern_boundary:LongPlatform", "platform_bern_short:LongPlatform",
            "platform_zh_unknown[platformLength -> ?L]", "sp_8509002:Junction",
            "sp_8509002[hasWaitingHall -> true]", 'sp_8503059[busyIn("2025") -> true]',
            "sp_8507000[nonStopTo -> sp_8509000]", "sp_8509000[nonStopTo -> sp_8503000]",
            "sp_8503059:LongDistanceStation", "sp_8507000[hasWifi -> true]",
        ):
            with self.subTest(goal=goal):
                self.assertEqual(self.client.query(f"?- {goal}.")["status"], "unknown")

    def test_hierarchy_and_standing_demolition_hall(self):
        for goal in ("platform_bern_long:Facility", "platform_bern_long:Entity",
                     "sp_8509000:Place", "sp_8503000[hasWaitingHall -> true]"):
            self.assertEqual(self.client.query(f"?- {goal}.")["status"], "true")

    def test_every_rule_family_has_traceable_evidence(self):
        for fact in (
            "platform_bern_long:LongPlatform", "sp_8509000[hasWaitingHall -> true]",
            "sp_8509000:Junction", 'sp_8505300[busyIn("2025") -> true]',
            'sp_8507000[servedByCategory -> "IC"]', "sp_8507000:LongDistanceStation",
            "sp_8507000[nonStopTo -> sp_8503000]", "sp_8503059:Interchange",
        ):
            with self.subTest(fact=fact):
                explanation = self.client.explain(fact)
                self.assertIn("Derived by rule", explanation)
                self.assertIn("Asserted fact", explanation)

    def test_schema_values(self):
        self.assertEqual(schema_failures(self.client.validate()), [])

    def test_missing_real_data_fails_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "scripts/ingest.py"):
                inputs("sbb", directory)


class Counterfactuals(unittest.TestCase):
    """Remove the evidence behind a true conclusion; the conclusion must not survive.

    Each case edits one sample fact. Under the open world, the conclusion must become
    unknown, not false. The check that the goal is true beforehand keeps a broken
    rule or a typo in the goal from passing as unknown.
    """

    CASES = (
        # (goal, text in sample_facts.fx, replacement)
        ("sp_8509000[hasWifi -> true]", "hasWifi -> true; servedByLine", "servedByLine"),
        ("sp_8509000:Junction", "\n    servedByLine -> line_920;", ""),
        ("platform_bern_long:LongPlatform", "platformLength -> 321.0", "platformLength -> 320.0"),
        ("sp_8507000[nonStopTo -> sp_8503000]", "; nextStop -> event_ic_2", ""),
        ('sp_8503000[servedByCategory -> "TGV"]', "event_tgv:StopEvent[ofRun -> run_tgv; ",
         "event_tgv:StopEvent["),
        ("sp_8507000:LongDistanceStation", 'category -> "IC"', 'category -> "S"'),
        ('sp_8505300[busyIn("2025") -> true]', 'observedFrequency("2025") -> 20001.0',
         'observedFrequency("2025") -> 20000.0'),
        ("sp_8509000[hasWaitingHall -> true]", 'sp_8509000; status -> "BESTEHEND"',
         'sp_8509000; status -> "PROJEKTIERT NEU"'),
        ("sp_8503000[hasWaitingHall -> true]", 'sp_8503000; status -> "PROJEKTIERT ABBRUCH"',
         'sp_8503000; status -> "PROJEKTIERT NEU"'),
        ("sp_8503059:Interchange", "servesMode -> mode_train; servesMode -> mode_tram;",
         "servesMode -> mode_train;"),
    )

    @classmethod
    def setUpClass(cls):
        files, _ = inputs()
        cls.source = "\n".join(path.read_text(encoding="utf-8") for path in files)
        cls.client, _ = load_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_removing_evidence_removes_the_conclusion(self):
        for goal, old, new in self.CASES:
            with self.subTest(goal=goal):
                self.assertEqual(self.client.query(f"?- {goal}.")["status"], "true")
                self.assertEqual(self.source.count(old), 1, f"edit must hit exactly one fact: {old!r}")
                with Client(retain_transcript=False) as client:
                    client.load_program(source=self.source.replace(old, new))
                    self.assertEqual(client.query(f"?- {goal}.")["status"], "unknown")


@unittest.skipUnless(os.environ.get("RUN_SBB_TESTS") == "1", "set RUN_SBB_TESTS=1 for cached SBB data")
class SBBQuestions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = json.loads((ROOT / "tests" / "expected.json").read_text())
        manifest = json.loads((ROOT / "data" / "facts" / "manifest.json").read_text())
        # Refuse stale expected answers and mixtures of independently refreshed exports.
        for name, dataset in manifest["datasets"].items():
            path = ROOT / "data" / "raw" / (dataset["dataset"] + ".json")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != dataset["raw_sha256"] or actual != cls.expected["raw_sha256"][name]:
                raise AssertionError(f"Stale snapshot for {name}; regenerate facts and expected answers")
        cls.client, cls.metadata = load_client("sbb")

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_all_18_answers_against_independent_raw_oracle(self):
        self.assertEqual(self.metadata["operating_days"], self.expected["operating_days"])
        for question in QUESTIONS:
            with self.subTest(question=question.id):
                result = self.client.query(question.query)
                if question.id == "1.7":
                    self.assertEqual(result["status"], "unknown")
                else:
                    actual = sorted([value(binding[key]) for key in question.compared]
                                    for binding in result.get("bindings", []))
                    self.assertEqual(actual, self.expected[question.id])

    def test_full_data_proofs(self):
        for fact in ('sp_8507000[servedByCategory -> "IC"]', "sp_8509002:Junction",
                     "sp_8507000[nonStopTo -> sp_8503000]"):
            explanation = self.client.explain(fact)
            self.assertIn("Derived by rule", explanation)
            self.assertIn("Asserted fact", explanation)


if __name__ == "__main__":
    unittest.main()
