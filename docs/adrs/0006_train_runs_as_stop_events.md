# 6. Model train runs as ordered stop events

Date: 2026-09-29

## Status

Accepted

## Context

The train export has one row per train run and stop, with scheduled times, a cancellation flag and a pass-through flag. Queries 1.4, 1.6, 3.3 and 3.4 ask where trains actually stopped and which stop came next.

Finding the next stop needs the stops in time order. A rule for "next" would need a negation (no stop in between), and the open world leaves a negation unknown (see [ADR 1](0001_open_world_assumption.md)). We did not test such a rule.

## Decision

- Group the rows by operating day and journey id.
- Drop cancelled stops (`faellt_aus_tf`) and pass-throughs (`durchfahrt_tf`), as the question sheet defines "actually stopped".
- Sort the remaining stops by scheduled arrival, or by scheduled departure where no arrival exists. Stops without any time or with equal times stop the ingestion.
- Write each stop as a `StopEvent` with `atStopPoint`, `ofRun` and its scheduled times. Link consecutive stops with `nextStop`.
- A stop outside the scope breaks the chain, so no link spans a foreign station.
- The rule `nonStopTo` links the stop points of two linked events of the same run. It has a direction and is not transitive.
- The rule `servedByCategory` follows from the events and the category of their run.

## Consequences

- `nextStop` is a source fact, not a conclusion. `--explain` shows it as asserted.
- A cancelled stop in the middle of a run links the stops before and after it.
- The train data makes up 394,007 of the 443,975 facts.
- The source only holds the previous day, so the answers to the four queries change daily. With several operating days in the data, the queries return the union.
