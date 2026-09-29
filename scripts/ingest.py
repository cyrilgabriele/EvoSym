"""Fetch SBB Open Data and write FrameX facts for Swiss passenger rail.

Each dataset becomes one fact file in data/facts/. The vocabulary follows
hackathon01/HA1_FrameX_SBB_Test_Queries.md. Only facts found in the data are
written; derived properties (nonStopTo, servedByCategory, hasWaitingHall,
LongPlatform, Junction, ...) belong in the rules.

    uv run python scripts/ingest.py            # use cached downloads
    uv run python scripts/ingest.py --refresh  # download everything again
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
FACTS_DIR = ROOT / "data" / "facts"
EXPORT_URL = "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/{}/exports/json"
WORLD = "world open."
# Service points served by these means of transport count as passenger rail.
RAIL_MODES = {"TRAIN", "RACK_RAILWAY"}
MAX_EXAMPLES = 15

DATASETS = {
    "stations": ("dienststellen-gemass-opentransportdataswiss",
                 "Service Points (Didok) based on opentransportdata.swiss"),
    "wifi": ("wifistation", "Wifi@Station"),
    "platforms": ("perron", "Stop: platform length (body)"),
    "waiting_halls": ("haltestelle-wartehallen", "Stop: waiting rooms"),
    "sector_boards": ("sektortafel", "Stop: sector boards"),
    "passenger_counts": ("passagierfrequenz", "Ein- und Aussteigende an Bahnhöfen"),
    "line_stops": ("linie-mit-betriebspunkten", "Line (Operation Points)"),
    "lines": ("linie", "SBB's route network"),
    "train_runs": ("ist-daten-sbb",
                   "Target/Actual Comparison SBB departure/arrival times: (previous day)"),
}


# --- download -----------------------------------------------------------------

def fetch(dataset_id: str, refresh: bool) -> tuple[list[dict], str]:
    path = RAW_DIR / f"{dataset_id}.json"
    if refresh or not path.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {dataset_id} ...", flush=True)
        with urllib.request.urlopen(EXPORT_URL.format(dataset_id), timeout=300) as response:
            path.write_bytes(response.read())
    retrieved = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return json.loads(path.read_text()), retrieved


# --- FrameX formatting -----------------------------------------------------------

def uic(value) -> int | None:
    """Stop-point numbers arrive as int, text or float (8505307.0)."""
    if value in (None, ""):
        return None
    return int(float(value))


def sp(number: int) -> str:
    return f"sp_{number}"


def string(text) -> str:
    text = " ".join(str(text).split())
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def number(value) -> str | None:
    value = float(value)
    return repr(value) if math.isfinite(value) else None


def slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text.lower())


def short_hash(*parts) -> str:
    return hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:12]


def fact(subject: str, attribute: str, value: str) -> str:
    return f"{subject}[{attribute} -> {value}]."


def member(obj: str, cls: str) -> str:
    return f"{obj}:{cls}."


class Dropped:
    """Collects rows the script leaves out so each fact file can say what it left out."""

    def __init__(self) -> None:
        self.rows = 0
        self.names: dict[int, str] = {}
        self.unnumbered: list[str] = []

    def add(self, number: int | None, name) -> None:
        if number is None:
            self.unnumbered.append(str(name))
            return
        self.rows += 1
        self.names.setdefault(number, str(name))

    def note(self) -> list[str]:
        notes = []
        if self.unnumbered:
            notes += [f"Dropped {len(self.unnumbered)} rows without a stop-point number:",
                      "  " + "; ".join(sorted(self.unnumbered))]
        if not self.rows:
            return notes or ["No rows outside the scope."]
        names = sorted(set(self.names.values()))
        more = f"; ... (+{len(names) - MAX_EXAMPLES})" if len(names) > MAX_EXAMPLES else ""
        return notes + [f"Dropped {self.rows} rows at {len(self.names)} stop points outside the "
                        f"scope (not a Swiss passenger rail stop point in Didok):",
                        "  " + "; ".join(names[:MAX_EXAMPLES]) + more]


# --- one builder per dataset -------------------------------------------------------

def build_stations(rows: list[dict]) -> tuple[list[str], list[str], dict[int, dict]]:
    scope = {}
    for r in rows:
        modes = set((r["meansoftransport"] or "").split("|"))
        if r["isocountrycode"] == "CH" and r["stoppoint"] == "true" and modes & RAIL_MODES:
            scope[r["number"]] = r
    facts, cantons = [], {}
    for n, r in sorted(scope.items()):
        s = sp(n)
        facts.append(member(s, "StopPoint"))
        facts.append(fact(s, "designation", string(r["designationofficial"])))
        if r["cantonabbreviation"]:
            canton = "canton_" + slug(r["cantonabbreviation"])
            cantons[canton] = r["cantonname"]
            facts.append(fact(s, "inCanton", canton))
        for mode in sorted(r["meansoftransport"].split("|")):
            facts.append(fact(s, "servesMode", "mode_" + slug(mode)))
    for canton, name in sorted(cantons.items()):
        facts.append(member(canton, "Canton"))
        facts.append(fact(canton, "designation", string(name)))
    notes = [f"Kept {len(scope)} of {len(rows)} service points: in CH, stoppoint = true, "
             f"meansoftransport contains {' or '.join(sorted(RAIL_MODES))}."]
    return facts, notes, scope


def build_wifi(rows, scope):
    dropped, stations = Dropped(), set()
    for r in rows:
        n = uic(r["bpuic"])
        if n in scope:
            stations.add(n)
        else:
            dropped.add(n, r["standort"])
    facts = [fact(sp(n), "hasWifi", "true") for n in sorted(stations)]
    notes = [f"{len(rows)} rows -> {len(stations)} stop points with WiFi.",
             "Open world: a missing row does not mean the station has no WiFi."]
    return facts, notes + dropped.note()


def build_platforms(rows, scope):
    dropped, facts, no_length = Dropped(), [], 0
    for r in sorted(rows, key=lambda r: r["fid"]):
        n = uic(r["bpuic"])
        if n not in scope:
            dropped.add(n, r["bps_name"])
            continue
        p = f"platform_{r['fid']}"
        facts.append(member(p, "Platform"))
        facts.append(fact(p, "atStopPoint", sp(n)))
        if r["p_nr"]:
            facts.append(fact(p, "platformNumber", string(r["p_nr"])))
        if r["p_lange"] is None:
            no_length += 1
        else:
            facts.append(fact(p, "platformLength", number(r["p_lange"])))
    notes = [f"One Platform per row (a physical platform, e.g. island platform \"10/11\"); id = fid.",
             f"{no_length} platforms have no length in the data, so no platformLength fact."]
    return facts, notes + dropped.note()


def build_waiting_halls(rows, scope):
    dropped, halls = Dropped(), {}
    for r in rows:
        n = uic(r["bpuic"])
        if n not in scope:
            dropped.add(n, r["bezeichnung_offiziell"])
            continue
        geo = r["geopos"] or {}
        key = short_hash(n, r["linie"], r["km"], r["gebaudename"], r["status"],
                         geo.get("lon"), geo.get("lat"))
        halls[f"waitinghall_{key}"] = (n, r["status"])
    facts = []
    for h, (n, status) in sorted(halls.items()):
        facts.append(member(h, "WaitingHall"))
        facts.append(fact(h, "atStopPoint", sp(n)))
        if status:
            facts.append(fact(h, "status", string(status)))
    notes = ["The data has no id, so the id is a hash of stop point, line, km, name, status "
             "and position.",
             "status is BESTEHEND (exists), PROJEKTIERT NEU (planned) or "
             "PROJEKTIERT ABBRUCH (planned for demolition)."]
    return facts, notes + dropped.note()


def build_sector_boards(rows, scope):
    dropped, facts = Dropped(), []
    for r in sorted(rows, key=lambda r: r["fid"]):
        n = uic(r["bpuic"])
        if n not in scope:
            dropped.add(n, r["bps_name"])
            continue
        b = f"sectorboard_{r['fid']}"
        facts.append(member(b, "SectorBoard"))
        facts.append(fact(b, "atStopPoint", sp(n)))
        if r["kundengleisnummer"]:
            facts.append(fact(b, "trackNumber", string(r["kundengleisnummer"])))
        if r["sektor_vorderseite"]:
            facts.append(fact(b, "sectorFront", string(r["sektor_vorderseite"])))
        if r["sektor_ruckseiter"]:
            facts.append(fact(b, "sectorBack", string(r["sektor_ruckseiter"])))
    return facts, ["One SectorBoard per row; id = fid."] + dropped.note()


def build_passenger_counts(rows, scope):
    dropped, values = Dropped(), defaultdict(set)
    for r in rows:
        n = uic(r["uic"])
        if n not in scope:
            dropped.add(n, r["bahnhof_gare_stazione"])
            continue
        if r["dtv_tjm_tgm"] is not None and r["jahr_annee_anno"]:
            values[(n, str(r["jahr_annee_anno"])[:4])].add(number(r["dtv_tjm_tgm"]))
    facts = [fact(sp(n), f"observedFrequency({string(year)})", v)
             for (n, year), vs in sorted(values.items()) for v in sorted(vs)]
    conflicts = sum(1 for vs in values.values() if len(vs) > 1)
    years = sorted({year for _, year in values})
    notes = ["observedFrequency(Year) = DTV (dtv_tjm_tgm): average people boarding plus "
             "alighting per day over all weekdays.",
             f"Years: {', '.join(years)}. Stop point/year pairs with conflicting values: {conflicts}."]
    return facts, notes + dropped.note()


def build_line_stops(rows, scope):
    dropped, pairs = Dropped(), set()
    for r in rows:
        n = uic(r["bpuic"])
        if n in scope:
            pairs.add((n, r["linie"]))
        else:
            dropped.add(n, r["bezeichnung_offiziell"])
    facts = [fact(sp(n), "servedByLine", f"line_{line}") for n, line in sorted(pairs)]
    notes = ["servedByLine = the stop point lies on this infrastructure line.",
             "Operating points that are not stations (junctions, sidings, crossovers) "
             "are out of scope."]
    return facts, notes + dropped.note()


def build_lines(rows, scope):
    facts = []
    for r in sorted(rows, key=lambda r: r["linie"]):
        line = f"line_{r['linie']}"
        facts.append(member(line, "Line"))
        facts.append(fact(line, "label", string(r["linie"])))
        if r["linienname"]:
            facts.append(fact(line, "lineName", string(r["linienname"])))
    return facts, [f"{len(rows)} lines of the SBB route network."]


def build_train_runs(rows, scope):
    runs = defaultdict(list)
    for r in rows:
        runs[r["fahrt_bezeichner"]].append(r)
    dropped = Dropped()
    facts, n_events, n_links, cancelled, passing = [], 0, 0, 0, 0
    for journey, stops in sorted(runs.items()):
        stops.sort(key=lambda r: r["ankunftszeit"] or r["abfahrtszeit"])
        run = f"run_{short_hash(journey)}"
        run_facts, previous, index = [], None, 0
        for r in stops:
            if r["faellt_aus_tf"]:
                cancelled += 1
                continue
            if r["durchfahrt_tf"]:
                passing += 1
                continue
            n = uic(r["bpuic"])
            if n not in scope:
                # Breaks the chain: no nextStop link across a stop outside the scope.
                dropped.add(n, r["haltestellen_name"])
                previous = None
                continue
            index += 1
            event = f"ev_{run[4:]}_{index}"
            run_facts += [member(event, "StopEvent"),
                          fact(event, "atStopPoint", sp(n)),
                          fact(event, "ofRun", run)]
            if previous:
                run_facts.append(fact(previous, "nextStop", event))
                n_links += 1
            previous = event
        if run_facts:
            facts += [member(run, "TrainRun"),
                      fact(run, "journeyId", string(journey)),
                      fact(run, "category", string(stops[0]["verkehrsmittel_text"]))]
            facts += run_facts
            n_events += index
    days = sorted({r["betriebstag"] for r in rows})
    notes = [f"Operating day(s): {', '.join(days)}. The dataset only holds the previous day.",
             f"{len(rows)} rows, {len(runs)} runs. Only actual stops are written: "
             f"{cancelled} cancelled stops (faellt_aus_tf) and {passing} pass-throughs "
             f"(durchfahrt_tf) are left out.",
             f"{n_events} StopEvents; ev[nextStop -> ev2] links consecutive actual stops of a run "
             f"in timetable order ({n_links} links)."]
    return facts, notes + dropped.note()


BUILDERS = {
    "wifi": build_wifi,
    "platforms": build_platforms,
    "waiting_halls": build_waiting_halls,
    "sector_boards": build_sector_boards,
    "passenger_counts": build_passenger_counts,
    "line_stops": build_line_stops,
    "lines": build_lines,
    "train_runs": build_train_runs,
}


# --- output ----------------------------------------------------------------------

def write_facts(name: str, retrieved: str, facts: list[str], notes: list[str]) -> Path:
    dataset_id, title = DATASETS[name]
    header = [WORLD,
              f"// Source: \"{title}\" (data.sbb.ch dataset {dataset_id}), retrieved {retrieved}.",
              "// Generated by scripts/ingest.py. Do not edit by hand.",
              *(f"// {line}" for line in notes),
              f"// {len(facts)} facts.",
              ""]
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = FACTS_DIR / f"{name}.fx"
    path.write_text("\n".join(header + facts) + "\n")
    return path


def check(paths: list[Path]) -> bool:
    if not shutil.which("framex"):
        print("framex not found on PATH; skipped the load check.", file=sys.stderr)
        return True
    ok = True
    for label, files in [*((p.name, [p]) for p in paths), ("all files together", paths)]:
        result = subprocess.run(["framex", "check", *map(str, files)],
                                capture_output=True, text=True)
        output = (result.stdout + result.stderr).strip()
        print(f"  check {label}: {output}")
        ok &= result.returncode == 0
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="download all datasets again")
    parser.add_argument("--no-check", action="store_true", help="skip the framex load check")
    args = parser.parse_args()

    rows, retrieved = fetch(DATASETS["stations"][0], args.refresh)
    facts, notes, scope = build_stations(rows)
    paths = [write_facts("stations", retrieved, facts, notes)]
    print(f"stations: {len(facts)} facts")
    for name, build in BUILDERS.items():
        rows, retrieved = fetch(DATASETS[name][0], args.refresh)
        facts, notes = build(rows, scope)
        paths.append(write_facts(name, retrieved, facts, notes))
        print(f"{name}: {len(facts)} facts")

    if args.no_check:
        return 0
    print("Checking that every fact file loads in FrameX:")
    return 0 if check(paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
