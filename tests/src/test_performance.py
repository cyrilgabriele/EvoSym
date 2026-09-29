"""The measurements run on the sample, so no SBB data is needed."""

import unittest

from src.performance import bars, measure, render
from src.queries import QUESTIONS


class Performance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = measure("sample", repeat=2)

    def test_every_question_and_rule_is_measured(self):
        self.assertEqual([row["id"] for row in self.report["queries"]], [q.id for q in QUESTIONS])
        self.assertEqual(len(self.report["explanations"]), 8)
        self.assertEqual(len(self.report["start_ms"]), 2)
        self.assertGreater(self.report["load"]["derived_facts"], 0)
        # Scaling cuts the SBB train data; the sample has none.
        self.assertEqual(self.report["scaling"], [])

    def test_report_names_every_question_and_escapes_text(self):
        page = render(self.report)
        for question in QUESTIONS:
            self.assertIn(f"{question.id} {question.title}", page)
        self.assertIn("busyIn(&quot;2025&quot;)", page)
        self.assertNotIn('busyIn("2025")', page)

    def test_bars_scale_to_the_largest_value(self):
        page = bars([("a", 1.0, ""), ("b", 4.0, "")], "s")
        self.assertIn("width: 25.0%", page)
        self.assertIn("width: 100.0%", page)


if __name__ == "__main__":
    unittest.main()
