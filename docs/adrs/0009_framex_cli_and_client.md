# 9. Run FrameX through the local CLI and a standard-library client

Date: 2026-09-29

## Status

Accepted

## Context

The course provides FrameX as a command-line program (version 0.4.3) and documents a [Python API](https://unisg-ics-dsnlp.github.io/FrameX-Doc/python/index.html). The PyPI package `framex` is unrelated. The hosted Workbench needs credentials and a network connection.

## Decision

- `src/framex.py` starts `framex serve` as a subprocess and exchanges JSON lines with it. It uses the standard library only. No inference happens in Python.
- The runner joins ontology, rules and facts into one program and loads it in pieces below the engine's request limit of 1 MB.
- For the full data the runner sets a limit of 2,000,000 proofs and a timeout of 300 seconds per request.
- The Workbench script `scripts/framex_workbench.py` stays an optional tool. The pipeline does not use it.

## Consequences

- The FrameX program must be on the `PATH`. See [local FrameX setup](../FRAME_X_LOCAL.md).
- Loading 443,975 facts and answering all 18 queries takes 7 seconds on an Apple Silicon laptop.
- With the default proof limit of the CLI, the full data stops with "proof limit reached". The CLI needs `--max-proofs`.
- Through the runner, `--explain` names the source of a fact as `<json-chunk>` with a line number. The CLI names the file and the line.
