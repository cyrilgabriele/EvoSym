# 3. Use stable identifiers across datasets

Date: 2026-09-29

## Status

Accepted

## Context

The datasets name the same station in different fields and types: `number` as an integer, `bpuic` as an integer, text or float, and `uic` as a float (`8502113.0`). Waiting halls have no id in the source. Queries join across datasets, so one entity needs one identifier.

## Decision

| Entity | Identifier |
| --- | --- |
| Stop point | `sp_<UIC>`, after converting the source value to a whole number without rounding. A value that is not a whole number stops the ingestion. |
| Platform, sector board | `platform_<fid>`, `sectorboard_<fid>`, from the feature id of the source |
| Waiting hall | `waitinghall_<hash>`: the first 20 hex digits of a SHA-256 hash over stop point, line, kilometre, building name and position |
| Train run | `run_<hash>` over operating day and journey id |
| Stop event | `ev_<hash>` over operating day, journey id, stop point and both scheduled times |
| Line, canton, mode | `line_<number>`, `canton_<abbreviation>`, `mode_<mode>` |

- Names are labels, never join keys.
- A platform is one physical platform. Platform "10/11" serves two tracks.
- The status is not part of a waiting hall's id. Two rows with the same id and different statuses stop the ingestion.

## Consequences

- A join across datasets is an equality of identifiers in the query.
- Identifiers do not depend on the order of the source rows.
- A waiting hall keeps its id when its status changes. It gets a new id when the source changes a hashed field.
- Our generated ids differ from the ids in the reference. The question sheet states that only entities and values should match.
