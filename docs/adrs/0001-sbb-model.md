# 0001 — SBB source facts and FrameX reasoning

Date: 2026-09-29. Status: implemented.

## Context

Cyril's task covers all 18 questions in the [hackathon PDF](../hackathon01/HA1_FrameX_SBB_Test_Queries.pdf). The downloaded exports use different stop identifier fields, mixed numeric representations, nullable values, and observations from different years. The existing local Python client runs the team FrameX executable. Pydantic was installed by the developer before implementation.

## Decisions

- Keep application code directly under `src/`. Put SBB-specific validation and conversion in `src/adapters/sbb/`; keep `scripts/ingest.py` as its command-line entry point. No separate domain model is needed for this pipeline.
- Validate all consumed source fields with Pydantic before generating files. Ignore unused extra fields. Fail with a dataset and row number for invalid values. Nullable source values remain absent facts. A missing country does not establish Swiss scope.
- Use `sp_<UIC>` across exports, joining `number`, `bpuic`, and `uic` after lossless integer normalization. Names are labels, never join keys. The scope is Swiss (`CH`) stop points marked `stoppoint=true` with `TRAIN` or `RACK_RAILWAY` service in Didok. Keep separate stop points separate, even when their names suggest a shared station complex.
- Use an open world. A missing WiFi record or measurement is unknown. Do not declare the WiFi export complete or infer `hasWifi=false` from absence.
- Keep classes and schemas in `ontology.fx`, deductions in `rules.fx`, and the 18 queries in `queries.py`. The adapter emits source observations and ordered event adjacency, not `LongPlatform`, `Junction`, `busyIn`, `hasWaitingHall`, `servedByCategory`, `LongDistanceStation`, `nonStopTo`, or `Interchange` conclusions.
- A platform is a physical platform identified by `fid`, possibly serving multiple tracks. Length is a float in metres. Sector boards retain separate `fid` identities and track numbers as strings.
- A waiting hall is identified by a hash of stop, infrastructure line, kilometre, building name, and coordinates. Status does not affect its ID. Colliding identities with conflicting statuses fail validation; no upstream persistent building ID is available. Both `BESTEHEND` and `PROJEKTIERT ABBRUCH` imply a standing hall; `PROJEKTIERT NEU` does not.
- Passenger frequency is DTV: mean daily boardings plus alightings across all days of the week. Store it as `observedFrequency("YYYY")`; retain conflicting values and report their count. The independent expectation builder refuses to silently choose between conflicting observations.
- `servedByLine` refers to infrastructure lines, not commercial train service names. A junction requires two distinct line IDs. An interchange requires both `TRAIN` and `TRAM` at the same service point. Long-distance categories are IC, IR, EC, ICE, TGV, NJ, RJ, RJX, making the PDF's open-ended category examples explicit.
- Group train events by operating day and journey ID. Exclude cancellations and pass-throughs as defined in the question sheet, sort actual stops by parsed scheduled arrival (departure when arrival is absent), and deduplicate repeated observations. An out-of-scope actual stop breaks adjacency. Missing or tied ordering timestamps fail instead of guessing. An event ID includes day, journey, stop, and scheduled timestamps.
- `nonStopTo` is directed adjacency of two actual stops on the same run. It is not transitive. Runs retain operating days and events retain timestamps. For multiple operating days, the supplied questions return the union of observed services across those days; the runner reports the days.
- Preserve `data/raw/` as cached snapshots. Ordinary ingestion performs no network calls. `--refresh` explicitly replaces downloads. Record raw hashes, source URLs, cached-file timestamps, fact hashes, row counts, exclusions, and operating days in `data/facts/manifest.json`. A file timestamp is only a retrieval-time proxy, not the dataset's publication date.
- Load either the handwritten sample or the nine generated fact files. Verify generated file hashes before loading. Use chunked loading through `src/framex.py`, with a finite limit of two million proofs for the full snapshot; retain no transport transcript for these large loads.

## Consequences

The sample is reproducible in Git and covers all 18 queries. Full-data tests use an independent calculation from the same cached JSON and verify snapshot hashes before comparison. Queries do not depend on parsing a Markdown or PDF file at runtime. Downloaded/generated data remain Git-ignored; a fresh checkout can run the sample immediately after dependency and CLI setup.

The chosen scope can exclude facilities associated with separate, inactive, or differently classified service points. Exclusions are reported in the manifest; they are not evidence that a facility or service does not exist. The question sheet's train references use 27 September 2026; this cached train export uses 28 September 2026. Reference answers guide semantics and cannot certify another snapshot.

## Sources

- [Hackathon question sheet](../hackathon01/HA1_FrameX_SBB_Test_Queries.pdf).
- Official FrameX documentation: [classes](https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/classes-subclasses.html), [rules](https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/rules.html), [open world](https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/world-assumption.html), [schema checks](https://unisg-ics-dsnlp.github.io/FrameX-Doc/tutorial/lesson-06-schema.html). Checked with the team CLI 0.4.3; numeric `Float` schema values are emitted as decimal literals.
