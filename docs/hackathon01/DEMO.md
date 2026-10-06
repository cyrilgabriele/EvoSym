# Demo

## TA queries that match the reference

```sh
# 1.1 Does Chur have WiFi? -> W = true
# 1.7 Long-distance stations without WiFi -> unknown (open world)
# 2.2 Platforms at Bern longer than 320 m -> 7 platforms (derived class LongPlatform)
# 3.1 Junctions in Graubünden -> Chur (900, 920), Landquart (900, 910, 920) (multi-hop: station -> canton, lines -> label)
uv run python src/main.py --source sbb --question 1.1 --question 1.7 --question 2.2 --question 3.1
```

## TA queries that differ from the reference

```sh
# 3.4 TGV stations -> adds Renens VD: our train data is from 30 Sept, the reference from 27 Sept
uv run python src/main.py --source sbb --question 3.4

# 2.4 Planned waiting halls in canton Bern -> adds 3 halls at Langenthal, the source marks them PROJEKTIERT NEU in BE
uv run python src/main.py --source sbb --question 2.4
```

## Oracle

```sh
# All 18 answers vs. answers computed from the raw SBB files without FrameX
RUN_SBB_TESTS=1 uv run python -m unittest -v tests.src.test_runner.SBBQuestions.test_all_18_answers_against_independent_raw_oracle
```

## Explanation

```sh
# Why Landquart is a junction: rule, bindings and the condition line_900 != line_910
uv run python src/main.py --source sbb --question 3.1 --explain 'sp_8509002:Junction' | sed -n '/^sp_8509002:Junction/,+3p'
```

## Counterfactual

```sh
# Passes: remove the evidence behind a true fact, the fact becomes unknown
uv run python -m unittest -v tests.src.test_runner.Counterfactuals

# Remove ?A != ?B from the Junction rule: a station on one line becomes a junction, the test fails ('true' != 'unknown')
sed -i '' '10s/ AND ?A != ?B\./\./' src/knowledge_base/rules.fx
uv run python -m unittest -v tests.src.test_runner.Counterfactuals

# Restore the rule
git checkout src/knowledge_base/rules.fx
```

## Everything

```sh
# All 18 TA queries
uv run python src/main.py --source sbb

# All tests, including oracle and counterfactuals
RUN_SBB_TESTS=1 uv run python -m unittest discover -v
```
