"""Load a reproducible knowledge base and run the shared question catalog."""

import hashlib
import json
from pathlib import Path

from .framex import Client
from .queries import QUESTIONS


ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "src" / "knowledge_base"
FACT_NAMES = ("stations", "wifi", "platforms", "waiting_halls", "sector_boards",
              "passenger_counts", "line_stops", "lines", "train_runs")


def inputs(source="sample", facts_dir=None):
    files = [KB / "ontology.fx", KB / "rules.fx"]
    if source == "sample":
        return files + [KB / "sample_facts.fx"], {"source": "sample", "synthetic": True}
    if source != "sbb":
        raise ValueError(f"Unknown source: {source}")
    directory = Path(facts_dir) if facts_dir is not None else ROOT / "data" / "facts"
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("SBB facts are missing. Run: uv run python scripts/ingest.py")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("format_version") != 1 or set(manifest.get("datasets", {})) != set(FACT_NAMES):
        raise ValueError("Incomplete or unsupported facts manifest; rerun scripts/ingest.py")
    for name in FACT_NAMES:
        path = directory / f"{name}.fx"
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["datasets"][name]["facts_sha256"]:
            raise ValueError(f"Missing or modified {path}; rerun scripts/ingest.py")
        files.append(path)
    return files, {"source": "sbb", "operating_days": manifest["operating_days"],
                   "raw_sha256": {name: item["raw_sha256"] for name, item in manifest["datasets"].items()}}


def load_client(source="sample", facts_dir=None):
    files, metadata = inputs(source, facts_dir)
    client = Client(retain_transcript=False, request_timeout=300,
                    max_response_bytes=256 * 1024 * 1024)
    try:
        client.load_program(source="\n".join(path.read_text(encoding="utf-8") for path in files),
                            max_proofs=2_000_000)
    except BaseException:
        client.close()
        raise
    return client, metadata


def run_questions(client, questions=QUESTIONS):
    return [{"id": question.id, "title": question.title,
             **client.query(question.query)} for question in questions]


def schema_failures(report):
    """Validation is a check of known facts, not an open-world completeness proof."""
    return [entry for entry in report.get("schema_checks", [])
            if entry["status"] == "violated"] + report.get("violations", [])
