"""Run all 18 SBB questions: uv run python src/main.py [--source sbb]."""

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.framex import FrameXError, FrameXTimeout
from src.queries import BY_ID, QUESTIONS
from src.runner import load_client, run_questions, schema_failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("sample", "sbb"), default="sample")
    parser.add_argument("--facts-dir", type=Path, help="SBB facts directory with manifest.json")
    parser.add_argument("--question", choices=tuple(BY_ID), action="append", help="Run selected question(s)")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--explain", help="Explain a fact, e.g. 'sp_8509000:Junction'")
    parser.add_argument("--validate", action="store_true", help="Also validate schema values")
    args = parser.parse_args(argv)
    if args.facts_dir is not None and args.source != "sbb":
        parser.error("--facts-dir requires --source sbb")
    questions = tuple(BY_ID[qid] for qid in dict.fromkeys(args.question)) if args.question else QUESTIONS
    try:
        client, metadata = load_client(args.source, args.facts_dir)
        with client:
            report = {**metadata, "questions": run_questions(client, questions)}
            if args.explain:
                report["explanation"] = client.explain(args.explain)
            failures = []
            if args.validate:
                validation = client.validate()
                failures = schema_failures(validation)
                report["validation"] = {"failures": failures, "coverage": validation["coverage"]}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Source: {args.source}" + (" (invented teaching data)" if args.source == "sample"
                  else f"; operating day(s): {', '.join(metadata['operating_days'])}"))
            for answer in report["questions"]:
                print(f"\n{answer['id']} {answer['title']}")
                print(f"  {answer['status']}; {len(answer.get('bindings', []))} result(s)")
                for binding in answer.get("bindings", []):
                    print("  " + ", ".join(f"{key} = {value}" for key, value in sorted(binding.items())))
            if "explanation" in report:
                print("\n" + str(report["explanation"]))
            if args.validate:
                print(f"\nSchema violations: {len(failures)}")
        return 1 if failures else 0
    except (OSError, ValueError, FrameXError, FrameXTimeout) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
