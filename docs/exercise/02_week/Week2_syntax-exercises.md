# Hackathon 1 prep exercises

Practice for the four capabilities from **VL02 · Symbolic foundations**:
REPRESENT, DERIVE, MODEL, DECIDE. Work through these Exercises before Hackathon 1 FlightMode (on paper, no FrameX-Workbench)!

A solution sheet will be uploaded after the Exercise session.

---

## 1. REPRESENT — facts, variables, joins

**1.1 Write it, then reverse it.**
Write a fact stating that `nadia` is `enrolledIn` `course_ai`. 

What is the object, attribute (named property), value?

Inverse it! What would you claim instead? Are these the
same fact? Explain in one sentence why direction matters here.

**1.2 Predict the bindings.**
Given:
```fx
nadia[enrolledIn -> course_ai].
tom[enrolledIn -> course_ai].
nadia[enrolledIn -> course_logic].
```
Predict every `(S, C)` pair returned by `?- ?S[enrolledIn -> ?C].`. 

How many bindings? What does each variable stand for?

**1.3 Build a join.**
Add `course_ai[taughtBy -> hoffmann].` to the world above. Write a query
that finds every student taught by `hoffmann`, joining through the shared
course variable. Which variable is the join?

**1.4 Break the join on purpose.**
Take your query from 1.3 and rename `?C` in one condition to `?C2`,
leaving the other as `?C`. What happens to the result, and why does that
prove the join was "just a shared variable" all along?

---

## 2. DERIVE — rules, recursion, rounds

**2.1 Write a one-hop rule.**
Using 1.3's world, write a rule `?S:AIStudent <- ...` that derives AI
student status from `enrolledIn`. Confirm it with a query.

**2.2 Make it recursive.**
Model a `prerequisiteOf` chain: `stats_101` is a prerequisite of `ml_201`,
which is a prerequisite of `nlp_301`. Write a base rule and a recursive
rule for `requiredBefore`, the way in VL02 `ancestor` was built from
`father`. State in words why one rule can't do it alone.

**2.3 Trace the rounds by hand.**
Before running anything, fill in this table for your rule from 2.2 (three
facts, so three names to chain):

| Round | New `requiredBefore` facts |
|---|---|
| 1 | ? |
| 2 | ? |
| 3 | ? (fixpoint?) |

Now run it. Where did your prediction diverge, if at all?

**2.4 Counterfactual.**
Delete the middle fact (`ml_201` requires `stats_101`, say). Predict which
derived pairs survive before re-running. Would removing a *derived* fact
directly (instead of a base fact) even be meaningful here? Why not?


---

## 3. MODEL — frames and the right entity

**3.1 Handle vs. label.**
Model two different courses that happen to share a display name
("Introduction to AI" offered in two different semesters). Give each its
own handle. Write the fact that would be wrong to write, and say what it
would incorrectly claim.

**3.2 Is this an attribute or its own entity?**
You need to record that `nadia` submitted assignment `hw3` late, with a
timestamp and a penalty. Would you put `submittedLate -> true` directly on
`nadia`, or model the submission as its own object? Justify it using the
lecture's birth-record argument (slide 25).

**3.3 Build the reified relation.**
Implement your answer to 3.2: define a `Submission` frame with
`ofStudent`, `assignment`, `submittedAt`, `penalty`, then write one
instance. Query for every late submission with `penalty > 0`.

**3.4 Add the three tools.**
For your `Submission` frame:
- add one `declare required` and one `declare functional` constraint that
  make sense for it,
- write a comparison rule (`?S:HeavyPenalty <- ... AND ?P > 20.`),
- write one parameterized method (e.g. `?student[gradeFor(?course) -> ?G]`).

---

## 4. DECIDE — open world, closed world, assumptions

**4.1 Predict before declaring anything.**
World is open by default. You have `nadia[submitted -> hw1].` and nothing
else. What does `?- tom[submitted -> hw1].` return? What does
`?- NOT tom[submitted -> hw1].` return, and why are these not opposites?

**4.2 Close only what you can justify.**
You have a complete list of students who **withdrew** from the course
(`closed class withdrawn.`), but only a partial list of who **submitted**
hw1. Write the rule for `?S:activelyEnrolled <- ?S:student AND NOT
?S:withdrawn.` Is this rule justified? Would the equivalent rule over
`submitted` be justified? Say why not.

**4.3 Find the bug.**
Here's a rule modeled on the lecture's broken wedding-guest rule:
```fx
?S:passing <- ?S[hasGrade -> ?G] AND ?G >= 60.
```
A teaching assistant says this correctly finds every passing student.
What's the flaw if `hasGrade` isn't recorded for every student yet? What
would `?S:passing` incorrectly return `unknown`?

**4.4 AND-of-groups, OR-within-group.**
A student is `eligibleForCertificate` if: (attended ≥ 8 sessions **OR**
has an instructor waiver) **AND** (submitted the final project). Model
this as two rules feeding one combining rule — don't collapse it into one
big `AND` chain. Then work through this table before running it:

| Student | ≥8 sessions | Waiver | Final submitted | Eligible? |
|---|---|---|---|---|
| A | true | unknown | true | ? |
| B | false | false | true | ? |
| C | true | unknown | unknown | ? |

**4.5 Name the assumption.**
For student C in 4.4, your rule should return `unknown`, not `false`.
Write one sentence explaining exactly which missing fact causes that, and
what closing the wrong slot would have cost you.

