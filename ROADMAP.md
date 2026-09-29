# Hackathon 1 build roadmap — Cyril

## Goal and current state

Answer all 18 questions in [the question sheet](docs/hackathon01/HA1_FrameX_SBB_Test_Queries.md): first with a small, hand-written FrameX sample, then with the downloaded SBB data.

The nine SBB JSON exports are already in `data/raw/`. They are local, Git-ignored snapshots. `scripts/ingest.py` already downloads and converts them into `data/facts/*.fx`, but its mappings and output have not yet been accepted as correct. Treat that script as an adapter to audit and improve. `src/knowledge_base/ontology.fx` and `rules.fx` are empty; `src/main.py` still runs a Socrates example. No extra Python dependency is currently declared.

## Raw data inventory

Counts below come from the current files in `data/raw/` (29 September 2026). The service-points export (91 MB) and previous-day train export (50 MB) deserve special care when loading and testing.

| File | Rows | Main fields to inspect | Intended facts |
| --- | ---: | --- | --- |
| `dienststellen-gemass-opentransportdataswiss.json` | 60,162 | `number`, `designationofficial`, `cantonabbreviation`, `meansoftransport`, `stoppoint` | Stop points, names, cantons, modes |
| `wifistation.json` | 79 | `bpuic` | Positive WiFi facts |
| `perron.json` | 1,570 | `fid`, `bpuic`, `p_nr`, `p_lange` | Platforms, stop links, lengths |
| `haltestelle-wartehallen.json` | 939 | `bpuic`, `status`, location fields | Waiting halls and statuses |
| `sektortafel.json` | 5,364 | `fid`, `bpuic`, `kundengleisnummer`, `sektor_vorderseite` | Sector boards |
| `passagierfrequenz.json` | 5,724 | `uic`, `jahr_annee_anno`, `dtv_tjm_tgm` | Passenger observations by year |
| `linie-mit-betriebspunkten.json` | 1,892 | `bpuic`, `linie` | Stop-to-line links |
| `linie.json` | 433 | `linie`, `linienname` | Line labels |
| `ist-daten-sbb.json` | 69,854 | `betriebstag`, `fahrt_bezeichner`, `bpuic`, times, cancellation and pass-through flags | Actual stop events and train runs |

## Steps

1. **Inventory all 18 questions.** For each ID, record the input datasets, required facts, any deduction, and the expected answer on a tiny sample. Ask Philipp to confirm source fields and data limits; ask Gian to specify positive, negative, and unknown cases. Use question 2.2 (long platforms at Bern) as the first vertical slice, then work through Levels 1, 2, and 3.

2. **Write the shared model.** Put the world assumption, classes, properties, and any supported schema declarations in `src/knowledge_base/ontology.fx`. Use the same stop ID in every dataset (`sp_<UIC>`); give platforms, halls, events, and runs their own IDs. Keep time-dependent observations tied to a year or operating day. Decide explicitly which data is incomplete: a missing WiFi row does not mean `false` in an open world. Check syntax against the [official FrameX documentation](https://unisg-ics-dsnlp.github.io/FrameX-Doc/index.html) and `framex check`.

3. **Create a tracked hand-written sample.** Add `src/knowledge_base/sample_facts.fx` with enough entities to exercise all 18 questions. Include a result that should be derived, a near miss, and a missing fact that should remain unknown. Keep this sample separate from generated `data/facts/` files so it stays reproducible in Git.

4. **Implement rules and query definitions.** Put deductions such as `LongPlatform`, `Junction`, `busyIn`, and `nonStopTo` in `src/knowledge_base/rules.fx`. Store all 18 query strings and expected sample results together in Python or a small tracked fixture. Run `framex check`, then each query and `framex explain` for representative derived answers. Do not precompute rule conclusions in the data adapter.

5. **Finish the Python runner.** Replace the Socrates example in `src/main.py`. Use the existing `src/framex.py` client to load ontology + rules + sample facts into one session, run all 18 queries, and print labelled answers. Make the input set selectable so the same queries can later run on generated facts. The first milestone is `uv run python src/main.py` succeeding with the hand-written sample.

6. **Audit and finish the SBB adapter.** Start from `scripts/ingest.py`; do not assume its existing mappings are correct. For all nine datasets, verify the raw field names and types, stop-ID normalization, stable entity IDs, string escaping, units, missing values, duplicate/conflicting rows, and filtering. Keep source and retrieval date in generated fact-file headers. In particular, verify that train events are grouped and ordered by operating day and run, and that cancelled or pass-through records do not create actual-stop links. Generate only asserted source facts. No new package is needed for the current JSON-to-facts path.

7. **Validate generated facts before full inference.** Run the adapter using cached `data/raw/`, inspect a few generated facts from each source, and run `framex check` on each file and the combined program. Compare key counts and spot checks with the raw rows. If a mapping is uncertain, record the assumption and resolve it with Philipp rather than silently dropping or changing rows.

8. **Run all 18 questions on SBB data.** Use the same runner and queries with `data/facts/*.fx`. Compare answers with the question sheet where the snapshot dates match. Explain at least one derived result per rule to Gian. Record discrepancies, open-world unknowns, data coverage, and the operating day of the previous-day train export.

9. **Document the reproducible commands.** Update `README.md` with the sample run, cached-data ingestion, optional refresh, full-data run, and the 18 supported questions. Mirror any source tests under `tests/` if tests are needed for nontrivial ID, date, or fact-generation logic.

## Completion check

- All 18 questions return their agreed answers on the tracked hand-written sample.
- Derived answers can be traced to rules and source facts; missing evidence stays unknown where appropriate.
- The same 18 queries run against generated facts from the downloaded SBB snapshots.
- A teammate can reproduce the sample run from a clean checkout with `uv` and the team-installed FrameX CLI.
