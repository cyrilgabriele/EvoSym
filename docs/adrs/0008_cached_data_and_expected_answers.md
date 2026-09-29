# 8. Cache downloads and test against independent expected answers

Date: 2026-09-29

## Status

Accepted

## Context

The SBB data changes. The train export is replaced every morning, and the reference solutions use 27 September 2026. The downloads take about 150 MB, too much for the repository. The course asks for correct and reproducible results.

## Decision

- `data/` is not part of the repository. Ingestion reads the downloads in `data/raw/`. Only `--refresh` downloads.
- `data/facts/manifest.json` records source addresses, hashes of downloads and fact files, row counts and operating days. The runner refuses a fact file whose hash differs from the manifest.
- The hand-written sample `src/knowledge_base/sample_facts.fx` is part of the repository and covers all 18 queries.
- `scripts/build_expected.py` computes the expected answers from the downloads. It uses neither FrameX nor the adapter nor the rules.
- `tests/expected.json` stores the hashes of the downloads it was built from. The tests refuse to compare against other downloads.
- The tests on the real data only run with `RUN_SBB_TESTS=1`.

## Consequences

- A fresh checkout runs the sample and its tests without a download.
- Every download needs a new run of `build_expected.py`. Two downloads of the same day can differ, which we observed on 29 September 2026.
- The expected-answer script repeats the scope and the thresholds in Python. A misread question would be wrong in both places and pass the tests.
- The reference solutions guide the meaning of the queries. They cannot confirm the answers of another day.
