"""Fetch SBB Open Data and write FrameX facts for Swiss passenger rail.

Each dataset becomes one fact file in data/facts/. The vocabulary follows
docs/hackathon01/HA1_FrameX_SBB_Test_Queries.pdf. Only facts found in the data are
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
from datetime import datetime, timezone
from pathlib import Path

from .models import identifier, validate_rows


ROOT = Path(__file__).resolve().parents[3]
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
    if refresh:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {dataset_id} ...", flush=True)
        with urllib.request.urlopen(EXPORT_URL.format(dataset_id), timeout=300) as response:
            content = response.read()
        json.loads(content)  # Do not replace a cached snapshot with an invalid response.
        temporary = path.with_suffix('.json.tmp')
        temporary.write_bytes(content)
        temporary.replace(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing cached export {path}; use --refresh to download.")
    retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    return json.loads(path.read_text()), retrieved


# --- FrameX formatting -----------------------------------------------------------

def uic(value) -> int | None:
    """Stop-point numbers arrive as int, text or float (8505307.0)."""
    return identifier(value)


def sp(number: int) -> str:
    return f"sp_{number}"


def string(text) -> str:
    return json.dumps(str(text), ensure_ascii=False)


def number(value) -> str:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("FrameX numeric facts must be finite")
    return repr(value)


def slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text.lower())


def short_hash(*parts) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()[:20]


def fact(subject: str, attribute: str, value: str) -> str:
    return f"{subject}[{attribute} -> {value}]."


def member(obj: str, cls: str) -> str:
    return f"{obj}:{cls}."


class Dropped:
    """Collects rows outside the scope so each fact file can say what it left out."""

    def __init__(self) -> None:
        self.rows = 0
        self.names: dict[int | None, str] = {}

    def add(self, number: int | None, name) -> None:
        self.rows += 1
        self.names.setdefault(number, str(name))

    def note(self) -> list[str]:
        if not self.rows:
            return ["No rows outside the scope."]
        names = sorted(set(self.names.values()))
        more = f", ... (+{len(names) - MAX_EXAMPLES})" if len(names) > MAX_EXAMPLES else ""
        return [f"Dropped {self.rows} rows at {len(self.names)} stop points outside the scope "
                f"(not a Swiss passenger rail stop point in Didok):",
                "  " + ", ".join(names[:MAX_EXAMPLES]) + more]


# --- one builder per dataset -------------------------------------------------------

def build_stations(rows: list[dict]) -> tuple[list[str], list[str], dict[int, dict]]:
    scope = {}
    for r in rows:
        modes = set((r["meansoftransport"] or "").split("|"))
        if r["isocountrycode"] == "CH" and r["stoppoint"] and modes & RAIL_MODES:
            if r["number"] in scope and scope[r["number"]] != r:
                raise ValueError(f"Conflicting service point rows for {r['number']}")
            scope[r["number"]] = r
    facts, cantons, transport_modes = [], {}, set()
    for n, r in sorted(scope.items()):
        s = sp(n)
        facts.append(member(s, "StopPoint"))
        facts.append(fact(s, "designation", string(r["designationofficial"])))
        if r["cantonabbreviation"]:
            canton = "canton_" + slug(r["cantonabbreviation"])
            cantons[canton] = r["cantonname"] or r["cantonabbreviation"]
            facts.append(fact(s, "inCanton", canton))
        for mode in sorted(r["meansoftransport"].split("|")):
            transport_modes.add("mode_" + slug(mode))
            facts.append(fact(s, "servesMode", "mode_" + slug(mode)))
    for mode in sorted(transport_modes):
        facts.append(member(mode, "TransportMode"))
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
    notes = [f"{len(rows)} rows -> {len(stations)} stop points with WiFi (duplicates merged).",
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
        key = short_hash(n, r["linie"], r["km"], r["gebaudename"],
                         geo.get("lon"), geo.get("lat"))
        if f"waitinghall_{key}" in halls and halls[f"waitinghall_{key}"] != (n, r["status"]):
            raise ValueError(f"Conflicting statuses for waiting hall {key}")
        halls[f"waitinghall_{key}"] = (n, r["status"])
    facts = []
    for h, (n, status) in sorted(halls.items()):
        facts.append(member(h, "WaitingHall"))
        facts.append(fact(h, "atStopPoint", sp(n)))
        if status:
            facts.append(fact(h, "status", string(status)))
    notes = ["The data has no id, so the id is a hash of stop point, line, km, name "
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
             "alighting per day over all days of the week.",
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
        runs[(r["betriebstag"], r["fahrt_bezeichner"])].append(r)
    dropped = Dropped()
    facts, n_events, n_links, cancelled, passing, duplicate_events = [], 0, 0, 0, 0, 0
    for (day, journey), rows_for_run in sorted(runs.items()):
        # Duplicated exports must not create extra stops or self-links.
        unique = {json.dumps(r, sort_keys=True, default=str): r for r in rows_for_run}
        duplicate_events += len(rows_for_run) - len(unique)
        stops = []
        for r in unique.values():
            if r["faellt_aus_tf"]:
                cancelled += 1
                continue
            if r["durchfahrt_tf"]:
                passing += 1
                continue
            if r["ankunftszeit"] is None and r["abfahrtszeit"] is None:
                raise ValueError(f"Missing stop order for {day}, {journey}")
            stops.append(r)
        if not stops:
            continue
        stops.sort(key=lambda r: r["ankunftszeit"] or r["abfahrtszeit"])
        times = [r["ankunftszeit"] or r["abfahrtszeit"] for r in stops]
        if len(set(times)) != len(times):
            raise ValueError(f"Ambiguous stop order for {day}, {journey}")
        categories = {r["verkehrsmittel_text"] for r in stops}
        if len(categories) != 1:
            raise ValueError(f"Conflicting categories for {day}, {journey}: {categories}")
        run = f"run_{short_hash(day, journey)}"
        run_facts, previous, index = [], None, 0
        for r in stops:
            n = uic(r["bpuic"])
            if n not in scope:
                # Breaks the chain: no nextStop link across a stop outside the scope.
                dropped.add(n, r["haltestellen_name"])
                previous = None
                continue
            index += 1
            event = f"ev_{short_hash(day, journey, n, r['ankunftszeit'], r['abfahrtszeit'])}"
            run_facts += [member(event, "StopEvent"),
                          fact(event, "atStopPoint", sp(n)),
                          fact(event, "ofRun", run)]
            for key, slot in (("ankunftszeit", "scheduledArrival"),
                              ("abfahrtszeit", "scheduledDeparture")):
                if r[key] is not None:
                    run_facts.append(fact(event, slot, string(r[key].isoformat())))
            if previous:
                run_facts.append(fact(previous, "nextStop", event))
                n_links += 1
            previous = event
        if run_facts:
            facts += [member(run, "TrainRun"),
                      fact(run, "journeyId", string(journey)),
                      fact(run, "operatingDay", string(day.isoformat())),
                      fact(run, "category", string(stops[0]["verkehrsmittel_text"]))]
            facts += run_facts
            n_events += index
    days = sorted({r["betriebstag"].isoformat() for r in rows})
    notes = [f"Operating day(s): {', '.join(days)}. The dataset only holds the previous day.",
             f"{len(rows)} rows, {len(runs)} runs. Only actual stops are written: "
             f"{cancelled} cancelled stops (faellt_aus_tf) and {passing} pass-throughs "
             f"(durchfahrt_tf) are left out.",
             f"Merged {duplicate_events} duplicate event rows. Grouped by operating day and journey id.",
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

def write_facts(name: str, retrieved: str, facts: list[str], notes: list[str], source_hash: str) -> Path:
    dataset_id, title = DATASETS[name]
    header = [WORLD,
              f"// Source: \"{title}\" ({EXPORT_URL.format(dataset_id)}).",
              f"// Cached file timestamp (UTC; retrieval proxy): {retrieved}.",
              f"// Raw SHA-256: {source_hash}.",
              "// Generated by scripts/ingest.py. Do not edit by hand.",
              *(f"// {line}" for line in notes),
              f"// {len(facts)} facts.",
              ""]
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = FACTS_DIR / f"{name}.fx"
    temporary = path.with_suffix('.fx.tmp')
    temporary.write_text("\n".join(header + facts) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def check(paths: list[Path]) -> bool:
    if not shutil.which("framex"):
        print("framex not found on PATH; install the team CLI or explicitly use --no-check.", file=sys.stderr)
        return False
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

    # Validate/build every source before replacing any fact files.
    outputs, manifest, scope = [], {"format_version": 1, "datasets": {}}, {}
    for name, (dataset, _) in DATASETS.items():
        raw_rows, retrieved = fetch(dataset, args.refresh)
        rows = validate_rows(name, raw_rows)
        if name == "stations":
            facts, notes, scope = build_stations(rows)
        else:
            facts, notes = BUILDERS[name](rows, scope)
        unique = list(dict.fromkeys(facts))
        raw_path = RAW_DIR / f"{dataset}.json"
        source_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        notes.append(f"Removed {len(facts) - len(unique)} repeated fact assertions.")
        outputs.append((name, retrieved, unique, notes, source_hash))
        manifest["datasets"][name] = {
            "dataset": dataset, "source_url": EXPORT_URL.format(dataset),
            "raw_sha256": source_hash, "cached_file_timestamp": retrieved,
            "raw_rows": len(raw_rows), "facts": len(unique), "notes": notes,
        }
        if name == "train_runs":
            manifest["operating_days"] = sorted({r["betriebstag"].isoformat() for r in rows})
        print(f"{name}: validated {len(rows)} rows, {len(unique)} facts", flush=True)
    paths = []
    for output in outputs:
        path = write_facts(*output)
        paths.append(path)
        manifest["datasets"][output[0]]["facts_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    if not args.no_check:
        print("Checking that every fact file loads in FrameX:")
        if not check(paths):
            return 1
    manifest["syntax_checked"] = not args.no_check
    manifest_path = FACTS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
