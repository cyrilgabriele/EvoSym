# 1. Use the open-world assumption

Date: 2026-09-29

## Status

Accepted

## Context

The course requires an explicit world assumption. The SBB exports are incomplete, and no dataset is declared complete. Example: six rows in Wifi@Station have no stop-point number (Altdorf; Genève, Cornavin; Rapperswil; St. Gallen; Wetzikon; Wil). These stations get no `hasWifi` fact although the dataset lists them. Under a closed world the system would claim that St. Gallen has no WiFi.

Test query 1.7 in the [question sheet](../hackathon01/HA1_FrameX_SBB_Test_Queries.pdf) expects `unknown`.

## Decision

- Every `.fx` file starts with `world open.` (see [FrameX: world assumption](https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/world-assumption.html)).
- The adapter writes positive facts only. It never writes a fact such as `hasWifi -> false`.
- An empty source value writes no fact.
- We declare no dataset complete.

## Consequences

- Query 1.7 (long-distance stations with no WiFi) returns `unknown`, as in the reference.
- Questions of the form "which stations lack X" cannot be answered until a dataset is declared complete for X.
- A derived term becomes true from positive evidence only. A station whose only hall is planned has an unknown `hasWaitingHall`, not a false one.
- `--validate` checks the known facts against the ontology. It does not prove that the data is complete.
