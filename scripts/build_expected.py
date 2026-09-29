"""Compute expected answers for the 17 TA test queries straight from the SBB API.

This is the test oracle. It reads raw SBB data and never touches FrameX, the
ingestion script or the rules, so a bug there cannot hide in the expected answers.
Writes tests/expected.json, keyed by query id (see hackathon01/HA1_FrameX_SBB_Test_Queries.md).

Each answer is a sorted list of rows, one row per expected binding, holding only
the variables the test compares. Stations are UIC numbers, numbers are floats.
Run it from the same data snapshot as the ingestion: train runs change daily.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = "https://data.sbb.ch/api/explore/v2.1/catalog/datasets"
OUT = ROOT / "tests" / "expected.json"

CHUR = 8509000
ZUERICH_HB = 8503000
BERN = 8507000

# Categories the TA reference counts as long-distance ("IC, IR, EC, ICE, TGV, NJ, RJX…").
LONG_DISTANCE = {"EC", "IC", "ICE", "IR", "NJ", "RJ", "RJX", "TGV"}
# Halls that physically exist; PROJEKTIERT NEU is planned but not built.
STANDING_HALL = {"BESTEHEND", "PROJEKTIERT ABBRUCH"}


def export(dataset: str, select: str, where: str | None = None) -> list[dict]:
    params = {"select": select}
    if where:
        params["where"] = where
    url = f"{API}/{dataset}/exports/json?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=300) as response:
        return json.load(response)


def uic(value) -> int | None:
    # passagierfrequenz stores UIC numbers as floats ("8502113.0"); some rows have none.
    return None if value is None else int(float(value))


def is_swiss(station: int) -> bool:
    return str(station).startswith("85")


def rows(values) -> list[list]:
    return sorted(list(v) if isinstance(v, tuple) else [v] for v in values)


def train_stations() -> dict[int, dict]:
    """Swiss service points with train service: the scope of the whole system."""
    points = export(
        "dienststellen-gemass-opentransportdataswiss",
        "number,cantonabbreviation,meansoftransport",
        'isocountrycode="CH"',
    )
    return {
        uic(p["number"]): p
        for p in points
        if "TRAIN" in (p["meansoftransport"] or "").split("|")
    }


def canton(stations: dict[int, dict], code: str) -> set[int]:
    return {s for s, p in stations.items() if p["cantonabbreviation"] == code}


def passenger_counts() -> dict[tuple[int, int], float]:
    """(station, year) -> DTV, the average daily boardings plus alightings over all days."""
    counts = export("passagierfrequenz", "uic,jahr_annee_anno,dtv_tjm_tgm")
    return {
        (uic(c["uic"]), int(c["jahr_annee_anno"][:4])): float(c["dtv_tjm_tgm"])
        for c in counts
        if c["uic"] is not None and c["dtv_tjm_tgm"] is not None
    }


def real_stops() -> tuple[str, list[dict]]:
    """Stops where a train actually halted: no pass-throughs, no cancellations."""
    runs = export(
        "ist-daten-sbb",
        "betriebstag,fahrt_bezeichner,bpuic,verkehrsmittel_text,"
        "ankunftszeit,abfahrtszeit,durchfahrt_tf,faellt_aus_tf",
    )
    days = {r["betriebstag"] for r in runs}
    assert len(days) == 1, f"expected one operating day, got {days}"
    stops = [
        r
        for r in runs
        if r["bpuic"] is not None and not r["durchfahrt_tf"] and not r["faellt_aus_tf"]
    ]
    for s in stops:
        s["bpuic"] = uic(s["bpuic"])
    return days.pop(), stops


def non_stop_pairs(stops: list[dict]) -> set[tuple[int, int]]:
    """Consecutive real stops of one run, both in Switzerland."""
    runs: dict[str, list[dict]] = {}
    for s in stops:
        runs.setdefault(s["fahrt_bezeichner"], []).append(s)
    pairs = set()
    for run in runs.values():
        # The first stop has no arrival time, the last no departure time.
        run.sort(key=lambda s: s["ankunftszeit"] or s["abfahrtszeit"])
        for here, there in zip(run, run[1:]):
            if is_swiss(here["bpuic"]) and is_swiss(there["bpuic"]):
                pairs.add((here["bpuic"], there["bpuic"]))
    return pairs


def main() -> None:
    stations = train_stations()
    day, stops = real_stops()
    counts = passenger_counts()
    pairs = non_stop_pairs(stops)
    wifi = {uic(w["bpuic"]) for w in export("wifistation", "bpuic")} - {None}
    halls = [
        (uic(h["bpuic"]), h["status"])
        for h in export("haltestelle-wartehallen", "bpuic,status")
        if uic(h["bpuic"]) in stations
    ]
    lines: dict[int, set[str]] = {}
    for op in export("linie-mit-betriebspunkten", "bpuic,linie"):
        if uic(op["bpuic"]) in stations:
            lines.setdefault(uic(op["bpuic"]), set()).add(str(op["linie"]))
    long_distance = {
        s["bpuic"]
        for s in stops
        if s["verkehrsmittel_text"] in LONG_DISTANCE and is_swiss(s["bpuic"])
    }

    zh_platforms = export("perron", "p_lange", f"bpuic={ZUERICH_HB}")
    bern_platforms = export("perron", "p_nr,p_lange", f"bpuic={BERN}")
    boards = export(
        "sektortafel", "sektor_vorderseite", f'bpuic={ZUERICH_HB} and kundengleisnummer="3"'
    )
    gr, ti, be, zh = (canton(stations, c) for c in ("GR", "TI", "BE", "ZH"))

    expected = {
        "operating_day": day,
        # Level 1
        "1.1": [["true"]] if CHUR in wifi else [],
        "1.2": rows(float(p["p_lange"]) for p in zh_platforms),
        "1.3": rows({s for s, status in halls if status in STANDING_HALL and s in gr}),
        "1.4": rows({s["verkehrsmittel_text"] for s in stops if s["bpuic"] == BERN}),
        "1.5": rows((s, v) for (s, y), v in counts.items() if y == 2024 and v > 50_000),
        "1.6": rows({b for a, b in pairs if a == BERN}),
        "1.7": "unknown",
        # Level 2
        "2.1": rows(wifi & ti),
        "2.2": rows(
            (p["p_nr"], float(p["p_lange"])) for p in bern_platforms if p["p_lange"] > 320
        ),
        "2.3": rows(b["sektor_vorderseite"] for b in boards),
        # One row per hall, so a station with two halls appears twice.
        "2.4": rows(s for s, status in halls if status == "PROJEKTIERT NEU" and s in be),
        "2.5": rows(s for s, status in halls if status == "PROJEKTIERT ABBRUCH" and s in zh),
        "2.6": rows(
            (s, counts[s, 2024])
            for s, ls in lines.items()
            if "900" in ls and (s, 2024) in counts
        ),
        # Level 3
        "3.1": rows((s, line) for s, ls in lines.items() if len(ls) >= 2 and s in gr for line in ls),
        "3.2": rows(
            (s, counts[s, 2018])
            for (s, y), v in counts.items()
            if y == 2025 and v > 20_000 and counts.get((s, 2018), 1e9) <= 20_000
        ),
        "3.3": rows({b for a, b in pairs if a == ZUERICH_HB and b in long_distance}),
        "3.4": rows(
            {s["bpuic"] for s in stops if s["verkehrsmittel_text"] == "TGV" and is_swiss(s["bpuic"])}
        ),
        "3.5": rows(
            s for s, p in stations.items() if "TRAM" in p["meansoftransport"].split("|")
        ),
    }
    OUT.write_text(json.dumps(expected, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} for operating day {day}")


if __name__ == "__main__":
    main()
