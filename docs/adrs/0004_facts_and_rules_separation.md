# 4. Keep source facts in the adapter and deductions in the rules

Date: 2026-09-29

## Status

Accepted

## Context

The task asks for a system that derives new facts from rules, with nothing hardcoded, and not for a queryable database. Computing a conclusion such as `LongPlatform` in Python during ingestion would be easy, but then no rule and no proof would stand behind the answer.

## Decision

- The adapter in `src/adapters/sbb/` writes only what the source states.
- `src/knowledge_base/ontology.fx` holds the classes, the class hierarchy and the typed properties.
- `src/knowledge_base/rules.fx` holds the eight rules. See [FrameX: rules](https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/rules.html).
- `src/queries.py` holds the 18 queries.
- The adapter writes none of the derived terms: `LongPlatform`, `hasWaitingHall`, `Junction`, `busyIn`, `servedByCategory`, `LongDistanceStation`, `nonStopTo`, `Interchange`.
- One exception: the order of the stops of a train run is computed in the adapter (see [ADR 6](0006_train_runs_as_stop_events.md)).

## Consequences

- Changing a threshold means editing one rule. The conclusions follow on the next load.
- Every derived answer has a proof that `--explain` prints.
- The fact files load on their own, without ontology and rules.
- Inference costs time and proofs when the data is loaded and queried (see [ADR 9](0009_framex_cli_and_client.md)).
