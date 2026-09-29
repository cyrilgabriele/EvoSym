# EvoSym - Evolvable Neuro-Symbolic Intelligence
Hybrid and Neuro-Symbolic Al Course @ HSG

## FrameX

The [official FrameX documentation](https://unisg-ics-dsnlp.github.io/FrameX-Doc/index.html) is the source of truth for FrameX syntax, APIs, and behavior.

Run the project entry point with `uv` from the repository root:

```sh
uv run python src/main.py
```

## Tests

The tests run the 17 TA test queries in `docs/hackathon01/HA1_FrameX_SBB_Test_Queries.md` against the ingested facts in `data/facts/` plus the ontology and rules in `src/knowledge_base/`. Code lives in a flat `src/` folder, so commands started from the repository root need `PYTHONPATH=src` to import `framex`:

```sh
PYTHONPATH=src uv run python -m unittest tests.test_questions
```

Run `uv run python scripts/ingest.py` first to create the facts. Expected answers in `tests/expected.json` come from the raw SBB data, independent of the knowledge base. The train-run dataset only holds the previous day, so regenerate them right after ingesting new data:

```sh
uv run python scripts/build_expected.py
```

The team uses the locally installed FrameX CLI for `.fx` programs. From the project root, verify the installation and run a program with:

```sh
framex --version
framex check path/to/program.fx
framex run path/to/program.fx
```

Version 0.4.3 is verified on the development machine. See [local FrameX setup](docs/FRAME_X_LOCAL.md) for installation and troubleshooting. For Python client code, use the separate [hosted Workbench workflow](docs/FRAME_X_WORKBENCH.md).
