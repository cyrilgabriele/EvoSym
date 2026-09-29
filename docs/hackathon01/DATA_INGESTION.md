# Data ingestion: SBB Open Data to FrameX facts

`scripts/ingest.py` downloads nine SBB Open Data datasets, filters them to Swiss passenger rail, cleans them and writes one FrameX fact file per dataset to `data/facts/`. This document records every change the script makes to the source data. The vocabulary follows the [test queries](HA1_FrameX_SBB_Test_Queries.md).

All numbers below come from the run on 29 September 2026. The train runs cover operating day 28 September 2026.

## Run

```sh
uv run python scripts/ingest.py            # use cached downloads in data/raw/
uv run python scripts/ingest.py --refresh  # download all datasets again
```

The script needs internet access and only the Python standard library. It stores each download unchanged as `data/raw/<dataset-id>.json`, writes `data/facts/<name>.fx`, and finally runs `framex check` on every file and on all files together. Query the facts with:

```sh
framex query data/facts/*.fx '?- sp_8509000[hasWifi -> ?W].'
```

## Principles

- **One fact file per dataset.** Each file starts with `world open.` and loads on its own.
- **Only what the data states.** Derived properties are left to the rules: `nonStopTo`, `servedByCategory`, `hasWaitingHall`, `LongPlatform`, `LongDistanceStation`, `Junction`, `busyIn` and `Interchange`.
- **No invented values.** A missing value produces no fact. The script never writes negative facts such as `hasWifi -> false`; under the open world, a missing fact means unknown.
- **Traceable.** Each file header records the source, retrieval date, filters, counts and the stop points it dropped. `framex explain` shows the file and line of every fact.

## Pipeline

1. **Download** each dataset as JSON from the Opendatasoft Explore API v2.1 export (`https://data.sbb.ch/api/explore/v2.1/catalog/datasets/<id>/exports/json`).
2. **Define the scope** as a list of Swiss passenger rail stop points taken from Didok (see below).
3. **Join and clean.** Every row is joined to that list by its stop-point number. Rows outside the scope are dropped and listed in the file header.
4. **Write facts** with the shared identifier `sp_<number>`. Strings are escaped (`\"`, `\\`) and whitespace is collapsed.
5. **Check** that every file loads in FrameX.

## Scope: which stop points count

Didok lists every public transport service point, including every bus stop and service points abroad. The script keeps a service point only if it is in Switzerland, is a stop point, and is served by train or rack railway:

| Filter | Dropped | Remaining |
| --- | ---: | ---: |
| All service points | | 60,162 |
| Not in Switzerland (DE 14,744, AT 9,358, FR 2,672, IT 450, no country 1,936) | 29,402 | 30,760 |
| Not a stop point (`stoppoint = false`: junctions, inventory and network points) | 3,678 | 27,082 |
| No `TRAIN` or `RACK_RAILWAY` in `meansoftransport` (mostly bus: 23,607) | 25,309 | **1,773** |

The mode counts overlap because one stop point can have several means of transport.

Boundary cases:

- **Combined stops stay in.** A stop point with both train and tram, such as "Zürich, Balgrist", is a station. Test query 3.5 (`Interchange`) depends on this.
- **Rack railways are in; funiculars (`CABLE_RAILWAY`, 138) and the Lausanne metro (`METRO`, 28) are out.** To change this, edit `RAIL_MODES` in the script.
- **The filter uses Didok's country, not the number prefix.** Some stations abroad carry a Swiss number (85…), for example Jestetten and Lottstetten in Germany. They are out of scope.

## Join key

All datasets identify stations by the seven-digit stop-point number, but in different fields and types. The script converts them all to `sp_<number>`:

| Dataset | Field | Type in the source |
| --- | --- | --- |
| Didok | `number` | integer |
| Wifi@Station, waiting rooms, Line (Operation Points) | `bpuic` | integer |
| Platform length, sector boards | `bpuic` | text |
| Passenger counts | `uic` | float (`8502113.0`) |
| Train runs | `bpuic` | float |

## Changes per dataset

### `stations.fx`: Service Points (Didok) based on opentransportdata.swiss

Dataset `dienststellen-gemass-opentransportdataswiss`, 60,162 rows.

- Keeps the 1,773 stop points described above.
- Writes `sp_<number>:StopPoint`, `designation` (from `designationofficial`), `inCanton -> canton_<abbreviation>` and one `servesMode -> mode_<mode>` per entry in `meansoftransport` (split at `|`, lower case).
- Adds the 26 cantons as objects: `canton_gr:Canton` with `designation -> "Graubünden"`.
- 7,167 facts.

### `wifi.fx`: Wifi@Station

Dataset `wifistation`, 79 rows.

- Writes `sp_<number>[hasWifi -> true]` for 73 stop points.
- Drops 6 rows without a stop-point number: Altdorf; Genève, Cornavin; Rapperswil; St. Gallen; Wetzikon; Wil (see known issues).
- 73 facts.

### `platforms.fx`: Stop: platform length (body)

Dataset `perron`, 1,570 rows.

- Drops 96 rows at 61 stop points outside the scope, leaving 1,474 platforms.
- Writes `platform_<fid>:Platform` (the source's feature id), `atStopPoint`, `platformNumber` (text, e.g. `"1/2"`) and `platformLength` (metres, as a float).
- One `Platform` is one physical platform: island platform "10/11" serves two tracks.
- 7 platforms have no length in the source and get no `platformLength` fact.
- 5,889 facts.

### `waiting_halls.fx`: Stop: waiting rooms

Dataset `haltestelle-wartehallen`, 939 rows.

- Drops 30 rows at 22 stop points outside the scope, leaving 909 waiting halls.
- The source has no id. The id `waitinghall_<hash>` is the first 12 hex digits of an MD5 hash over stop point, line, kilometre, building name, status and position.
- Writes `:WaitingHall`, `atStopPoint` and `status` as text: `BESTEHEND` (exists), `PROJEKTIERT NEU` (planned) or `PROJEKTIERT ABBRUCH` (planned for demolition).
- The dataset's own `kanton` field is not used. The canton always comes from Didok, so there is a single source for it.
- 2,727 facts.

### `sector_boards.fx`: Stop: sector boards

Dataset `sektortafel`, 5,364 rows.

- Drops 84 rows at 5 stop points outside the scope, leaving 5,280 boards.
- Writes `sectorboard_<fid>:SectorBoard`, `atStopPoint`, `trackNumber` (from `kundengleisnummer`), `sectorFront` (from `sektor_vorderseite`) and `sectorBack` (from `sektor_ruckseiter`). Empty values are skipped.
- 26,200 facts.

### `passenger_counts.fx`: Ein- und Aussteigende an Bahnhöfen

Dataset `passagierfrequenz`, 5,724 rows.

- Drops 42 rows at 13 stop points outside the scope.
- Writes `sp_<number>[observedFrequency("<year>") -> <DTV>]` for the years 2018, 2022, 2023, 2024 and 2025.
- DTV (`dtv_tjm_tgm`) is the average number of people boarding plus alighting per day over all days of the week. The weekday (DWV) and non-weekday (DNWV) averages are not written.
- No stop point has two different values for the same year.
- 5,682 facts.

### `line_stops.fx`: Line (Operation Points)

Dataset `linie-mit-betriebspunkten`, 1,892 rows.

- Drops 969 rows at 591 operating points that are not stations in scope, such as junctions (Abzw), crossovers (Spw) and freight yards.
- Writes `sp_<number>[servedByLine -> line_<number>]`: the stop point lies on this infrastructure line.
- 923 facts.

### `lines.fx`: SBB's route network

Dataset `linie`, 433 rows.

- Writes `line_<number>:Line`, `label` (the line number as text, e.g. `"900"`) and `lineName`.
- No scope filter: lines are infrastructure, not stop points.
- 1,299 facts.

### `train_runs.fx`: Target/Actual Comparison SBB departure/arrival times (previous day)

Dataset `ist-daten-sbb`, 69,854 rows for operating day 28 September 2026, 5,781 runs.

- Groups rows by run (`fahrt_bezeichner`) and sorts each run by planned arrival time, or departure time at the first stop.
- Keeps only actual stops. It drops 1,350 cancelled stops (`faellt_aus_tf`) and 32 further pass-throughs (`durchfahrt_tf`); a pass-through that is also cancelled counts as cancelled.
- Drops 3,930 rows at 284 stop points outside the scope, mostly abroad (for example the TGV stops in France).
- Writes 5,710 runs with at least one stop in scope: `run_<hash>:TrainRun`, `journeyId` (the source's `fahrt_bezeichner`) and `category` (from `verkehrsmittel_text`: IC, IR, S, …).
- Writes 64,542 stops: `ev_<run>_<n>:StopEvent`, `atStopPoint` and `ofRun`.
- Links consecutive actual stops of a run with `nextStop` (58,776 links). The chain breaks at a stop outside the scope, so no link spans a foreign station.
- 269,532 facts.

## Vocabulary written

| Term | Kind | Subject | File |
| --- | --- | --- | --- |
| `StopPoint` | class | `sp_<number>` | `stations.fx` |
| `designation` | attribute (text) | stop point, canton | `stations.fx` |
| `inCanton` | attribute → `canton_<xx>` | stop point | `stations.fx` |
| `servesMode` | attribute → `mode_<mode>` | stop point | `stations.fx` |
| `Canton` | class | `canton_<xx>` | `stations.fx` |
| `hasWifi` | attribute (`true`) | stop point | `wifi.fx` |
| `Platform` | class | `platform_<fid>` | `platforms.fx` |
| `platformNumber`, `platformLength` | attribute (text, number) | platform | `platforms.fx` |
| `WaitingHall` | class | `waitinghall_<hash>` | `waiting_halls.fx` |
| `status` | attribute (text) | waiting hall | `waiting_halls.fx` |
| `SectorBoard` | class | `sectorboard_<fid>` | `sector_boards.fx` |
| `trackNumber`, `sectorFront`, `sectorBack` | attribute (text) | sector board | `sector_boards.fx` |
| `atStopPoint` | attribute → stop point | platform, waiting hall, sector board, stop event | several |
| `observedFrequency(Year)` | parameterised attribute (number) | stop point | `passenger_counts.fx` |
| `servedByLine` | attribute → `line_<number>` | stop point | `line_stops.fx` |
| `Line`, `label`, `lineName` | class, attributes (text) | `line_<number>` | `lines.fx` |
| `TrainRun`, `journeyId`, `category` | class, attributes (text) | `run_<hash>` | `train_runs.fx` |
| `StopEvent`, `ofRun`, `nextStop` | class, attributes → run / stop event | `ev_<run>_<n>` | `train_runs.fx` |

## Validation

- All nine files load in FrameX 0.4.3, alone and together: 319,492 facts.
- With simple test-only rules for the derived terms, 14 of the 18 test queries return exactly the reference solution: 1.1, 1.2, 1.3, 1.5, 1.7, 2.1, 2.2, 2.3, 2.5, 2.6, 3.1, 3.2, 3.4 and 3.5.
- 1.4, 1.6 and 3.3 differ slightly because the reference uses operating day 27 September and these facts use 28 September. For example, Bern has no `TER` service and `nonStopTo` returns Bern Wankdorf instead of Lyss.
- 2.4 returns Langenthal in addition to the reference (see known issues).
- Loading the train runs together with rules needs `--max-proofs 1000000`. Without it, FrameX stops with "proof limit reached".

## Known issues and limitations

1. **WiFi rows without a stop-point number.** Six Wifi@Station rows have an empty `bpuic`: Altdorf, Genève (Cornavin), Rapperswil, St. Gallen, Wetzikon and Wil. These stations get no `hasWifi` fact, so their WiFi is unknown even though the dataset lists it. A documented manual mapping from name to stop point would fix this.
2. **Train runs change daily.** The source only holds the previous day, so running the script on another day produces a different `train_runs.fx`. `data/` is currently in `.gitignore`, so each team member generates their own copy.
3. **Incomplete waiting-hall rows.** Langenthal has three planned halls (`PROJEKTIERT NEU`) without building name, type or street. The script keeps them because stop point, canton and status are present. The reference solution for 2.4 does not list Langenthal.
4. **Waiting-hall ids are hashes.** They change if the source changes any of the hashed fields.
5. **Dropped stop points.** Rows at stop points outside the scope are not errors. Examples are operating points without passenger service (Basel SBB RB, Chiasso Smistamento), the underground stations Zürich HB Löwenstrasse and Museumstrasse, which Didok does not mark as stop points, and the German stations Jestetten and Lottstetten. Each fact file header lists the dropped stop points.
