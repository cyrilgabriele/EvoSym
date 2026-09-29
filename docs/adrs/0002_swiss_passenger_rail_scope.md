# 2. Limit the scope to Swiss passenger rail stop points

Date: 2026-09-29

## Status

Accepted

## Context

Didok lists 60,162 service points. Most are bus stops, points abroad or operating points without passenger service. The other datasets also refer to such points, for example freight yards, track junctions and the French stops of a TGV. The test queries ask about stations.

## Decision

- A stop point is in scope if Didok states country `CH`, `stoppoint = true` and a `meansoftransport` that contains `TRAIN` or `RACK_RAILWAY`. This keeps 1,773 stop points.
- The filter uses Didok's country, not the number prefix. A row without a country is out of scope.
- Rows of the other datasets at a stop point outside the scope are dropped. Each fact file header and `data/facts/manifest.json` report how many and which.
- Separate stop points stay separate, even when their names suggest one station.

## Consequences

- Query 3.4 lists only the Swiss TGV stations, as in the reference.
- Query 1.2 returns the 9 platforms of Zürich HB without the underground stations Löwenstrasse and Museumstrasse, as in the reference.
- A dropped row is not evidence that a facility or service does not exist.
- A train stop outside the scope breaks the chain of stops (see [ADR 6](0006_train_runs_as_stop_events.md)).
- Funiculars and the Lausanne metro are out. Changing this means editing `RAIL_MODES` in `src/adapters/sbb/ingest.py`.
- The counts per filter are in the [ingestion document](../hackathon01/DATA_INGESTION.md#scope-which-stop-points-count).
