# Hackathon 1 — team roles

**Challenge:** Derive from Knowledge. Turn a messy, real-world open dataset into a queryable reasoning system that derives new facts from rules and can explain its conclusions.

| Contributor | Course role | Mandate |
| --- | --- | --- |
| Cyril | **Developer** | Own the software and FrameX architecture, integrate the reasoning framework, and keep the code runnable, structured, and extensible. |
| Philipp | **Domain Expert** | Understand the dataset and its limits, turn domain questions into system requirements, and identify missing or unreliable data early. |
| Gian | **Auditor** | Design test questions and queries, check that derived facts follow from the rules and evidence, and define how the system's correctness will be evaluated. |

These are areas of ownership, not exclusive tasks. The team should agree on the ontology, world assumptions, and examples together during FlightMode. Roles rotate after each hackathon so that each person works in every role once.

## Handoffs for this hackathon

- **Philipp → Cyril:** dataset fields, data-quality limitations, domain questions, and the facts, classes, and relations needed to answer them.
- **Cyril → Gian:** runnable ingestion, ontology, rules, and queries, with enough provenance to trace each derived answer to its rule and source facts.
- **Gian → team:** test queries, expected outcomes, counterexamples, and any unsupported conclusions or gaps in the model.

The shared target is more than a searchable dataset: it needs rule-based derivation, explicit open- or closed-world assumptions, multi-hop queries, and explainable results. The course also calls for reproducibility, portability, and reasonable loading and inference performance.

## Working setup and timeline

- **Before the hackathon:** Prepare Git, `uv`, Python, the project template, and familiarity with the FrameX Python API. Review facts, rules, queries, ontology design, and open- versus closed-world reasoning. The [week 2 prep exercises](../../exercise/02_week/Week2_syntax-exercises.md) cover REPRESENT, DERIVE, MODEL, and DECIDE.
- **FlightMode, first hour:** Work on paper without phones, laptops, or coding agents. Sketch the ontology, example facts and rules, and the solution outline; hand in the concept at the checkpoint.
- **Remaining three hours:** Build and iterate. Submit cleaned, reproducible code and a README with the project overview and run instructions by the course deadline. Coding agents are allowed only after FlightMode; declare the tool and model in the submitted README if used.
- **After the hackathon:** Write the short LaTeX report in IMRaD form and prepare the demo slides for the next studio session.

**Setup gap to resolve:** The [course slides](../../exercise/02_week/02_HybridAI_Studio.pdf) call for Python 3.12, while this repository currently specifies Python 3.14 in `.python-version` and `pyproject.toml`. Confirm the required version before the build session. FrameX is also not yet declared as a project dependency.

Source: [Hybrid AI Studio, week 2](../../exercise/02_week/02_HybridAI_Studio.pdf), especially slides 7–14 (task, roles, requirements, timeline, deliverables, and preparation).
