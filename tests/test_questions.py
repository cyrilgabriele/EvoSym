"""Run the 17 TA test queries against the knowledge base.

Queries are read verbatim from docs/hackathon01/HA1_FrameX_SBB_Test_Queries.md, so
the knowledge base must use the TA vocabulary (sp_<UIC>, atStopPoint, ...).
Expected answers come from scripts/build_expected.py, which reads the raw SBB
data independently of ingestion and rules. Run with:

    PYTHONPATH=src uv run python -m unittest tests.test_questions

Loads every .fx file under data/facts/ (from scripts/ingest.py) and src/knowledge_base/
(ontology and rules). Override with FRAMEX_KB=dir1:dir2.
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

from framex import Client


ROOT = Path(__file__).resolve().parents[1]
KB_DIRS = [
    Path(d)
    for d in os.environ.get(
        "FRAMEX_KB", f"{ROOT / 'data' / 'facts'}{os.pathsep}{ROOT / 'src' / 'knowledge_base'}"
    ).split(os.pathsep)
]
EXPECTED = json.loads((ROOT / "tests" / "expected.json").read_text())
QUERY_FILE = ROOT / "docs" / "hackathon01" / "HA1_FrameX_SBB_Test_Queries.md"

# The variables each test compares; the rest (names, internal IDs) are ignored.
COMPARED = {
    "1.1": ["W"],
    "1.2": ["L"],
    "1.3": ["S"],
    "1.4": ["C"],
    "1.5": ["S", "V"],
    "1.6": ["B"],
    "2.1": ["S"],
    "2.2": ["No", "L"],
    "2.3": ["F"],
    "2.4": ["S"],
    "2.5": ["S"],
    "2.6": ["S", "V"],
    "3.1": ["S", "LL"],
    "3.2": ["S", "V"],
    "3.3": ["B"],
    "3.4": ["S"],
    "3.5": ["S"],
}


def read_queries() -> dict[str, str]:
    text = QUERY_FILE.read_text()
    found = re.findall(r"^### (\d\.\d) .*?```framex\n(.*?)\n```", text, re.S | re.M)
    return dict(found)


def value(raw: str):
    """Engine binding -> the oracle's form: sp_8507000 -> 8507000, '"IC"' -> 'IC', '420' -> 420.0."""
    if raw.startswith("sp_"):
        return int(raw.removeprefix("sp_"))
    if raw.startswith('"'):
        return raw.strip('"')
    try:
        return float(raw)
    except ValueError:
        return raw


def load_kb() -> Client:
    files = sorted(f for d in KB_DIRS for f in d.rglob("*.fx"))
    if not files:
        raise FileNotFoundError(f"no .fx files under {KB_DIRS}")
    client = Client(retain_transcript=False, request_timeout=300)
    client.load_program(source="\n".join(f.read_text() for f in files))
    return client


class TAQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queries = read_queries()
        cls.client = load_kb()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_all_17_queries_found(self):
        self.assertEqual(sorted(self.queries), sorted([*COMPARED, "1.7"]))

    def test_queries(self):
        for qid, variables in COMPARED.items():
            with self.subTest(query=qid):
                result = self.client.query(self.queries[qid])
                bindings = result.get("bindings", [])
                actual = sorted([value(b[v]) for v in variables] for b in bindings)
                self.assertEqual(actual, EXPECTED[qid], f"{qid}: {self.queries[qid]}")

    def test_1_7_missing_wifi_is_unknown_under_open_world(self):
        result = self.client.query(self.queries["1.7"])
        self.assertEqual(result["status"], EXPECTED["1.7"])


class Explanations(unittest.TestCase):
    """Requirement 6: a derived fact traces back to its rule and asserted facts."""

    @classmethod
    def setUpClass(cls):
        cls.client = load_kb()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def assertTraced(self, fact: str):
        text = str(self.client.explain(fact))
        self.assertIn("Derived by rule", text, text)
        self.assertIn("Asserted fact", text, text)

    def test_non_stop_connection(self):
        self.assertTraced("sp_8507000[nonStopTo -> sp_8503000]")

    def test_category_served(self):
        self.assertTraced('sp_8507000[servedByCategory -> "IC"]')

    def test_junction_builds_on_lines(self):
        self.assertTraced("sp_8509002:Junction")


if __name__ == "__main__":
    unittest.main()
