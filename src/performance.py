"""Measure engine start, loading, queries and explanations, and write an HTML report.

    uv run python src/performance.py                # hand-written sample
    uv run python src/performance.py --source sbb   # full SBB data, takes about a minute
"""

import argparse
import html
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.framex import Client
from src.queries import BY_ID, QUESTIONS
from src.runner import ROOT, inputs


OUTPUT = ROOT / "docs" / "hackathon01" / "performance.html"
MAX_PROOFS = 2_000_000
# Shares of the train data, the largest dataset, loaded on top of all other facts.
TRAIN_SHARES = (0.0, 0.25, 0.5, 0.75, 1.0)
# One derived fact per rule. All of them hold in the sample and in the SBB data.
EXPLAINED = (
    "sp_8509000[hasWaitingHall -> true]",
    "sp_8509000:Junction",
    'sp_8505300[busyIn("2025") -> true]',
    'sp_8507000[servedByCategory -> "IC"]',
    "sp_8507000:LongDistanceStation",
    "sp_8507000[nonStopTo -> sp_8503000]",
    "sp_8503059:Interchange",
)


# --- measuring --------------------------------------------------------------------

def new_client():
    return Client(retain_transcript=False, request_timeout=300,
                  max_response_bytes=256 * 1024 * 1024)


def seconds(action):
    started = time.perf_counter()
    result = action()
    return time.perf_counter() - started, result


def memory_mb(client):
    """Memory held by the engine process. None where `ps` does not exist (Windows)."""
    if shutil.which("ps") is None:
        return None
    shown = subprocess.run(["ps", "-o", "rss=", "-p", str(client.process.pid)],
                           capture_output=True, text=True, check=True)
    return int(shown.stdout) / 1024


def measure_start(repeat):
    """Start the engine and load an empty program: the time until it can answer."""
    times = []
    for _ in range(repeat):
        started = time.perf_counter()
        client = new_client()
        client.load("world open.")
        times.append((time.perf_counter() - started) * 1000)
        client.close()
    return times


def measure_load(source):
    """Load one program into a new engine. The caller closes the returned client."""
    client = new_client()
    took, loaded = seconds(lambda: client.load_program(source=source, max_proofs=MAX_PROOFS))
    stats = client.stats()
    return client, {
        "load_seconds": took,
        # The engine reports how long it evaluated the rules.
        "rule_seconds": stats["elapsed_micros"] / 1_000_000,
        "facts": loaded["facts"],
        "derived_facts": stats["derived_facts"],
        "rounds": stats["rounds"],
        "rule_firings": stats["rule_firings"],
        "memory_mb": memory_mb(client),
    }


def measure_queries(client, repeat):
    rows = []
    for question in QUESTIONS:
        times = []
        for _ in range(repeat):
            took, answer = seconds(lambda: client.query(question.query))
            times.append(took * 1000)
        rows.append({"id": question.id, "title": question.title, "status": answer["status"],
                     "results": len(answer.get("bindings", [])), "first_ms": times[0],
                     "median_ms": statistics.median(times), "max_ms": max(times)})
    return rows


def measure_explanations(client, repeat):
    # Platform ids differ between sample and SBB data, so take one from the answer to 2.2.
    platform_id = client.query(BY_ID["2.2"].query)["bindings"][0]["P"]
    rows = []
    for fact in (f"{platform_id}:LongPlatform", *EXPLAINED):
        times = []
        for _ in range(repeat):
            took, explanation = seconds(lambda: client.explain(fact))
            times.append(took * 1000)
        rows.append({"fact": fact, "median_ms": statistics.median(times),
                     "characters": len(str(explanation))})
    return rows


def measure_scaling(files):
    train = next(path for path in files if path.name == "train_runs.fx")
    others = "\n".join(path.read_text(encoding="utf-8") for path in files if path != train)
    lines = train.read_text(encoding="utf-8").splitlines()
    rows = []
    for share in TRAIN_SHARES:
        # The file holds one fact per line, so a cut between lines leaves a valid program.
        part = "\n".join(lines[:int(len(lines) * share)])
        client, row = measure_load(others + "\n" + part)
        with client:
            took, _ = seconds(lambda: [client.query(q.query) for q in QUESTIONS])
        rows.append({"share": share, "queries_ms": took * 1000, **row})
    return rows


def measure(source="sample", facts_dir=None, repeat=20):
    files, metadata = inputs(source, facts_dir)
    read_seconds, text = seconds(
        lambda: "\n".join(path.read_text(encoding="utf-8") for path in files))
    client, load = measure_load(text)
    with client:
        queries = measure_queries(client, repeat)
        explanations = measure_explanations(client, repeat)
        validate_seconds, _ = seconds(client.validate)
    version = subprocess.run(["framex", "--version"], capture_output=True, text=True, check=True)
    return {
        "source": source,
        "operating_days": metadata.get("operating_days", []),
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.release()}, {platform.machine()}, "
                   f"{os.cpu_count()} cores",
        "python": platform.python_version(),
        "framex": version.stdout.strip(),
        "repeat": repeat,
        "megabytes": len(text.encode("utf-8")) / 1_000_000,
        "start_ms": measure_start(repeat),
        "read_seconds": read_seconds,
        "load": load,
        "queries": queries,
        "explanations": explanations,
        "validate_seconds": validate_seconds,
        "scaling": measure_scaling(files) if source == "sbb" else [],
    }


# --- report -----------------------------------------------------------------------

STYLE = """
:root { color-scheme: light; --surface: #fcfcfb; --panel: #ffffff; --text: #0b0b0b;
  --muted: #52514e; --line: #e4e3df; --series: #2a78d6; }
@media (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --surface: #1a1a19; --panel: #232322; --text: #ffffff;
    --muted: #c3c2b7; --line: #3a3a38; --series: #3987e5; } }
* { box-sizing: border-box; }
body { margin: 0; padding: 32px 16px 64px; background: var(--surface); color: var(--text);
  font: 15px/1.5 system-ui, sans-serif; }
main { max-width: 1000px; margin: 0 auto; }
h1 { font-size: 28px; margin: 0 0 4px; }
h2 { font-size: 18px; margin: 40px 0 4px; }
p { margin: 0 0 12px; color: var(--muted); max-width: 70ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;
  margin-top: 24px; }
.tile, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }
.tile { padding: 14px 16px; }
.tile b { display: block; font-size: 26px; font-weight: 600; font-variant-numeric: tabular-nums; }
.tile span { color: var(--muted); font-size: 13px; }
.panel { padding: 16px; overflow-x: auto; }
.row { display: grid; grid-template-columns: minmax(7rem, 24rem) 1fr 6.5rem; gap: 10px;
  align-items: center; padding: 3px 0; font-size: 13px; }
.row:hover { background: var(--surface); }
.track { height: 14px; }
.bar { display: block; height: 14px; min-width: 2px; background: var(--series);
  border-radius: 0 4px 4px 0; }
.value { font-variant-numeric: tabular-nums; color: var(--muted); }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { padding: 6px 10px; border-bottom: 1px solid var(--line); text-align: left; }
th { color: var(--muted); font-weight: 500; }
td.number, th.number { text-align: right; font-variant-numeric: tabular-nums; }
details { margin-top: 12px; }
summary { cursor: pointer; color: var(--muted); font-size: 13px; }
"""


def bars(rows, unit):
    """Horizontal bars for (label, value, tooltip) rows, scaled to the largest value."""
    largest = max(value for _, value, _ in rows) or 1
    return '<div class="panel">' + "".join(
        f'<div class="row" title="{html.escape(tip)}"><span>{html.escape(label)}</span>'
        f'<span class="track"><span class="bar" style="width: {value / largest * 100:.1f}%">'
        f'</span></span><span class="value">{value:,.2f} {unit}</span></div>'
        for label, value, tip in rows) + "</div>"


def table(header, rows):
    """Text cells align left, numbers right."""
    def cell(tag, value):
        number = ' class="number"' if isinstance(value, (int, float)) else ""
        shown = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}" if isinstance(value, int) else value
        return f"<{tag}{number}>{html.escape(str(shown))}</{tag}>"
    body = "".join("<tr>" + "".join(cell("td", value) for value in row) + "</tr>" for row in rows)
    # A header cell is right-aligned when its column holds numbers.
    head = "".join(f'<th{" class=number" if rows and isinstance(rows[0][i], (int, float)) else ""}>'
                   f"{html.escape(name)}</th>" for i, name in enumerate(header))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def tile(value, label):
    return f'<div class="tile"><b>{html.escape(value)}</b><span>{html.escape(label)}</span></div>'


def render(report):
    load, queries = report["load"], report["queries"]
    start = statistics.median(report["start_ms"])
    median_query = statistics.median(row["median_ms"] for row in queries)
    other_seconds = load["load_seconds"] - load["rule_seconds"]
    memory = "unknown" if load["memory_mb"] is None else f'{load["memory_mb"]:,.0f} MB'
    days = ", operating day " + ", ".join(report["operating_days"]) if report["operating_days"] else ""

    parts = [
        f"<h1>FrameX performance</h1><p>Source: {html.escape(report['source'])}{days}. "
        f"Measured {html.escape(report['measured'])}.</p>",
        '<div class="tiles">',
        tile(f"{start:.1f} ms", "Engine start"),
        tile(f'{load["load_seconds"]:.2f} s', "Load and derive"),
        tile(f'{load["facts"]:,}', "Facts after loading"),
        tile(f'{load["derived_facts"]:,}', "of them derived by rules"),
        tile(f"{median_query:.2f} ms", "Median query"),
        tile(memory, "Engine memory"),
        "</div>",

        "<h2>Time per step</h2>"
        f"<p>The engine derives all conclusions when it loads the program: "
        f"{load['rule_firings']:,} rule firings in {load['rounds']} rounds. "
        "A query then only looks up facts.</p>",
        bars([
            ("Read the files from disk", report["read_seconds"],
             f"{report['megabytes']:.1f} MB of FrameX text"),
            ("Send, parse and index", other_seconds, "Load time minus the rule evaluation"),
            ("Evaluate the rules", load["rule_seconds"], "As reported by the engine"),
            ("Validate against the ontology (optional)", report["validate_seconds"],
             "Not part of loading, runs with --validate"),
        ], "s"),
    ]

    if report["scaling"]:
        parts += [
            "<h2>Loading time by data volume</h2>"
            "<p>Growing shares of the train data, the largest dataset, on top of all other "
            "facts. Each step starts a new engine.</p>",
            bars([(f"{row['share']:.0%} of the train data, {row['facts']:,} facts",
                   row["load_seconds"], f"Rules: {row['rule_seconds']:.2f} s")
                  for row in report["scaling"]], "s"),
            "<details><summary>Table</summary>",
            table(["Train data", "Facts", "Derived", "Load (s)", "Rules (s)",
                   "All 18 queries (ms)", "Memory (MB)"],
                  [[f"{row['share']:.0%}", row["facts"], row["derived_facts"], row["load_seconds"],
                    row["rule_seconds"], row["queries_ms"],
                    "unknown" if row["memory_mb"] is None else round(row["memory_mb"])]
                   for row in report["scaling"]]),
            "</details>",
        ]

    parts += [
        "<h2>Time per query</h2>"
        f"<p>Median of {report['repeat']} runs on the loaded data.</p>",
        bars([(f"{row['id']} {row['title']}", row["median_ms"],
               f"{row['results']} results, first run {row['first_ms']:.2f} ms, "
               f"slowest {row['max_ms']:.2f} ms") for row in queries], "ms"),
        "<details><summary>Table</summary>",
        table(["Query", "Question", "Status", "Results", "First run (ms)", "Median (ms)",
               "Slowest (ms)"],
              [[row["id"], row["title"], row["status"], row["results"], row["first_ms"],
                row["median_ms"], row["max_ms"]] for row in queries]),
        "</details>",

        "<h2>Time per explanation</h2>"
        f"<p>One derived fact per rule, median of {report['repeat']} runs.</p>",
        bars([(row["fact"], row["median_ms"], f"{row['characters']:,} characters of proof")
              for row in report["explanations"]], "ms"),

        "<h2>Setup</h2>",
        '<div class="panel">',
        table(["Item", "Value"], [
            ["Machine", report["machine"]],
            ["FrameX", report["framex"]],
            ["Python", report["python"]],
            ["Proof limit", f"{MAX_PROOFS:,}"],
            ["Program size", f"{report['megabytes']:.1f} MB"],
            ["Engine start", "Start the process and load an empty program, "
                             f"median of {report['repeat']} starts"],
            ["Engine memory", "Resident memory of the engine process after loading"],
        ]),
        "</div>",
    ]
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>FrameX performance</title><style>{STYLE}</style></head>"
            f'<body><main>{"".join(parts)}</main></body></html>\n')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=("sample", "sbb"), default="sample")
    parser.add_argument("--facts-dir", type=Path, help="SBB facts directory with manifest.json")
    parser.add_argument("--repeat", type=int, default=20, help="runs per query and explanation")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="HTML report to write")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    report = measure(args.source, args.facts_dir, args.repeat)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(report), encoding="utf-8")
    load = report["load"]
    print(f"Engine start: {statistics.median(report['start_ms']):.1f} ms")
    print(f"Load: {load['load_seconds']:.2f} s for {load['facts']:,} facts "
          f"({load['derived_facts']:,} derived)")
    print(f"Median query: {statistics.median(r['median_ms'] for r in report['queries']):.2f} ms")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
