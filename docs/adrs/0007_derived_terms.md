# 7. Define the derived terms

Date: 2026-09-29

## Status

Accepted

## Context

The [question sheet](../hackathon01/HA1_FrameX_SBB_Test_Queries.pdf) names derived classes and properties but leaves details open. It lists the long-distance categories as "IC, IR, EC, ICE, TGV, NJ, RJX…" and does not say whether a planned hall counts as a waiting hall.

## Decision

| Term | True when |
| --- | --- |
| `LongPlatform` | The platform is longer than 320 m |
| `hasWaitingHall` | A hall at the stop point has the status `BESTEHEND` or `PROJEKTIERT ABBRUCH` |
| `Junction` | The stop point lies on at least two different infrastructure lines |
| `busyIn(Year)` | The stop point had more than 20,000 daily passengers in that year |
| `servedByCategory` | A train run of that category actually stopped there |
| `LongDistanceStation` | The stop point is served by IC, IR, EC, ICE, TGV, NJ, RJ or RJX |
| `nonStopTo` | See [ADR 6](0006_train_runs_as_stop_events.md) |
| `Interchange` | The service point serves both train and tram |

- Daily passengers are DTV (`dtv_tjm_tgm`): the average number of people boarding plus alighting per day over all days of the week.
- `servedByLine` refers to infrastructure lines, not to commercial train services.

## Consequences

- The thresholds are strict. A platform of exactly 320 m is not long, and 20,000 passengers are not busy. The sample facts contain both cases.
- A hall planned for demolition still stands and counts. A planned new hall does not.
- The list of long-distance categories is closed. A new category needs an edit of the rule.
- Large stations such as Zürich HB are no interchanges, because their tram stops are separate service points.
- With the weekday average (DWV) instead of DTV, query 1.5 would also return Biel/Bienne, according to the question sheet.
