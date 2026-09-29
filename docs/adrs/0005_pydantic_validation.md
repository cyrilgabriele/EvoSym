# 5. Validate source rows with Pydantic

Date: 2026-09-29

## Status

Accepted

## Context

The SBB exports have empty values and mixed types, and their format can change without notice. A silent conversion could write wrong facts, for example a missing platform length as 0. The course also asks for minimal dependencies.

## Decision

- `src/adapters/sbb/models.py` has one Pydantic model per dataset.
- A model declares only the fields the adapter uses. Other fields are ignored.
- An invalid row stops the ingestion with the dataset name and the row number.
- An empty value stays empty and writes no fact.
- All nine datasets are validated before any fact file is replaced.

## Consequences

- A format change at SBB stops the ingestion instead of writing wrong facts. The model must then be updated before new data can be ingested.
- Pydantic is the only Python dependency of the project. It contains compiled code, so it needs a build for the target platform. Hand-written checks with the standard library would avoid this.
- The FrameX client `src/framex.py` and `scripts/build_expected.py` use the standard library only.
