# EvoSym - Evolvable Neuro-Symbolic Intelligence
Hybrid and Neuro-Symbolic AI Course @ HSG, Hackathon 1: Derive from Knowledge

## Overview

EvoSym turns nine SBB Open Data exports into a FrameX knowledge base and answers the 18 TA test queries in the [question sheet](docs/hackathon01/HA1_FrameX_SBB_Test_Queries.pdf). Answers are derived by rules, and every derived answer can be explained down to its rule and source facts.

1. `scripts/ingest.py` downloads the exports from data.sbb.ch, validates every field it uses and writes one fact file per dataset to `data/facts/`.
2. `src/knowledge_base/ontology.fx` declares the world assumption, the class hierarchy and the typed properties. `src/knowledge_base/rules.fx` holds the eight derivation rules.
3. `src/main.py` loads ontology, rules and facts into FrameX and runs the queries in `src/queries.py`.

| Path | Content |
| --- | --- |
| `src/knowledge_base/` | Ontology, rules and a small hand-written sample of facts |
| `src/adapters/sbb/` | Validation and conversion of the SBB exports |
| `src/queries.py`, `src/runner.py`, `src/main.py` | The 18 queries, the loader and the command line |
| `src/performance.py` | Performance measurements and their HTML report |
| `src/framex.py` | Python client for the FrameX engine, standard library only |
| `scripts/` | Entry points for ingestion and for the expected answers |
| `tests/` | Tests, mirroring the paths in `src/` |
| `docs/adrs/` | Architecture decision records |
| `docs/hackathon01/DATA_INGESTION.md` | Every change made to the source data |

## Setup

You need Python 3.12 or newer, [uv](https://docs.astral.sh/uv/) and the FrameX CLI 0.4.3 on your `PATH`. See [local FrameX setup](docs/FRAME_X_LOCAL.md) for the installation. Do not install the PyPI package `framex`, it is unrelated.

```sh
uv sync
framex --version
```

The [official FrameX documentation](https://unisg-ics-dsnlp.github.io/FrameX-Doc/index.html) is the source of truth for FrameX syntax, APIs, and behavior.

## Run

Run all commands from the repository root. The sample needs no download:

```sh
uv run python src/main.py
```

For the real SBB data, download and convert it first:

```sh
uv run python scripts/ingest.py --refresh
uv run python src/main.py --source sbb
```

`--refresh` downloads about 150 MB to `data/raw/`. Without it the script reuses these downloads and stops if they are missing. `data/` is not part of the repository.

| Option | Effect |
| --- | --- |
| `--source sbb` | Use the facts in `data/facts/` instead of the sample |
| `--question 2.2` | Run one question, repeatable |
| `--explain 'sp_8509002:Junction'` | Print the proof of a fact: rule, bindings and source facts |
| `--validate` | Check the facts against the ontology, exit code 1 on a violation |
| `--json` | Print a machine-readable report |

```sh
uv run python src/main.py --question 2.2 --explain 'platform_bern_long:LongPlatform'
```

Measured on an Apple Silicon laptop: download and ingestion take 22 seconds, loading 443,975 facts and answering all 18 queries takes 7 seconds.

`src/performance.py` measures engine start, loading, queries and explanations. It writes the [performance report](docs/hackathon01/performance.html):

```sh
uv run python src/performance.py --source sbb
```

## Tests

```sh
uv run python -m unittest discover
```

This runs the tests on the sample and the adapter. They need no data. The tests on the real data are skipped unless you prepare the data and set `RUN_SBB_TESTS=1`:

```sh
uv run python scripts/ingest.py --refresh
uv run python scripts/build_expected.py
RUN_SBB_TESTS=1 uv run python -m unittest discover
```

`scripts/build_expected.py` computes the expected answers in `tests/expected.json` from the raw SBB data. It uses neither FrameX nor the adapter nor the rules, so an error there cannot hide in the expected answers. The file stores the hashes of the downloads it was built from, and the tests refuse to compare against other downloads. Run `build_expected.py` after every `--refresh`, because the train data changes daily.

## Requirements

| Requirement | Where |
| --- | --- |
| Data ingestion | `src/adapters/sbb/`: API download, validation, one stop identifier across all datasets |
| Ontology | `src/knowledge_base/ontology.fx` |
| Rule-based derivation | `src/knowledge_base/rules.fx`. The adapter writes source facts only |
| World assumption | `world open.` in every file. Query 1.7 returns `unknown` |
| Multi-hop queries | Query 3.3 chains stop events, train runs, categories and two derived terms |
| Explainability | `--explain` |
| Performance | See the measurements above |
| Correctness | Tests and expected answers computed independently from the raw data |
| Portability | One Python dependency (Pydantic) and the FrameX CLI |

## Results against the reference

On our data of 29 September 2026, 14 of the 18 queries return exactly the reference solution. The others differ:

- **1.4, 1.6 and 3.3** use train data. The source only holds the previous day. Our data covers operating day 28 September 2026, the reference covers 27 September 2026.
- **2.4** also returns three planned halls at Langenthal. Their source rows state canton BE and status `PROJEKTIERT NEU`, so we keep them.

## Known limitations

- `--explain` names the source of a fact as `<json-chunk>` with a line number, because the Python runner loads all files as one program. The FrameX CLI names the file and line:

  ```sh
  framex explain --max-proofs 2000000 src/knowledge_base/ontology.fx src/knowledge_base/rules.fx data/facts/*.fx 'platform_35292761:LongPlatform'
  ```

- The order of the stops of a train run is computed during ingestion and written as `nextStop` facts. The rule `nonStopTo` derives from these facts.
- Data limitations are listed in [the ingestion document](docs/hackathon01/DATA_INGESTION.md#known-issues-and-limitations).

## Open world

We use the open-world assumption because this is a real-world dataset and we cannot ensure that no data is missing, so a missing fact means unknown, not false.

## Coding agents

Gian used Claude with the models Opus 5.5 and Fable 5.1 for the tests, the expected-answer script, the performance report, the README and the ADRs.

Filipp used Claude with the model Opus 5.5 for the data cleaning and data gathering.

Cyril used Codex with the model Astra-6 for the logic.
