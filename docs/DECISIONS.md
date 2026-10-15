# Decisions

Each decision: context, decision, tradeoff, result. Numbers come from saved runs in `runs/` and `reports/`.

## 1. A separate, installable harness instead of a third copy of eval code

- **Context.** Project 1 and Project 2 each have their own eval runner, metric code and report format. A third
  project would mean a third copy, and nothing would stop a change in one project from lowering quality silently.
- **Decision.** One small package, `hoteleval`, with a shared case schema, a metric registry, statistics, gates and
  reports. The core is standard library only, so a project's CI installs it in seconds.
- **Tradeoff.** The projects' own evals stay as they are (their published numbers must not change), so for now
  there are two ways to score each project.
- **Result.** Both projects' CI run the harness gates at tag v1.0.0 next to their own checks.

## 2. Reuse each project's metric code at a pinned commit, byte for byte

- **Context.** Re-implementing "answer accuracy" or "fact grounding" would create a second definition that could
  quietly disagree with the published one.
- **Decision.** `scripts/sync_vendor.py` copies the projects' metric files at pinned commits (Project 1 `5f9cd91`,
  Project 2 `575a19f`) into `hoteleval/vendor/`, changing only import lines, and records the original file hashes.
  `--check` fails if a copy drifts.
- **Tradeoff.** Some code is duplicated; a project fix reaches the harness only when the pin moves.
- **Result.** The harness reproduces the published numbers from the same recordings: Project 1 answer accuracy
  159/162 (98%), strict retrieval 44/45 per run, refusals 27/27, escalation rules 54/54; Project 2 escalation,
  injection and no-promise 100%, routing 98%, citations 94%, p50 4.6 s, $1.30 per 1,000 emails
  (`tests/test_reproduce.py`).

## 3. Pinned commits instead of new tags in the project repos

- **Context.** The brief asked to run each project "at a pinned git tag". Project 1's last tag is v1.4.0 (its
  shipped content is 1.5.0), and the rules allow only one change in the project repos: the harness CI job.
- **Decision.** Pin full commit SHAs in `hoteleval/pins.py`. Live runs export that commit with `git archive`, so the
  project checkout is never touched.
- **Tradeoff.** A SHA is less readable than a tag.
- **Result.** No tags or files were added to the project repos apart from the CI job.

## 4. One schema; labelled fields keep their original names

- **Context.** The two projects label different things (expected passage vs expected tools and tasks).
- **Decision.** Every case shares `id, project, property, category, split, input, expected.behaviour, tags, origin`;
  everything else a project labelled stays in `expected` under its original name, and `Case.native()` hands the
  project's metric code exactly what it expects.
- **Tradeoff.** `expected` is not uniform across projects.
- **Result.** Import changes nothing about what a case tests (`scripts/import_cases.py --check` rebuilds the files
  from the pinned commits and compares).

## 5. Recorded mode is the default; Project 1 retrieval is recomputed, not stored

- **Context.** Project 1's recorded answers keep the answer and citations but not the retrieved passages, timings
  or tokens.
- **Decision.** Retrieval, the scope check and the escalation rules are deterministic, so the Project 1 driver
  recomputes them at the pinned commit (no API) when a run is imported. Latency and cost for that run are shown as
  "from Project 1's own report" instead of being invented.
- **Tradeoff.** The imported Project 1 baseline has no per-answer latency.
- **Result.** CI never calls the API and every gate is reproducible.

## 6. Intervals over distinct cases, not cases × runs

- **Context.** Running the same 40 emails three times gives 120 outputs, but not 120 independent samples of the
  emails guests might send.
- **Decision.** Rates are pooled over runs; 95% Wilson intervals use the number of distinct cases.
- **Tradeoff.** Wider intervals: 8 must-escalate emails at 100% give 68–100%.
- **Result.** The dashboard shows how little a small group proves instead of hiding it.

## 7. Gates: hard 100%, floors, the baseline interval, and stable flips

- **Context.** A pure interval check is lenient on small sets. Measured before building the gate: lowering
  Project 1's top-k from 5 to 2 drops strict retrieval from 44/45 to 42/45 (q13, q35 lost). 93% is inside the
  baseline interval (88–100%), so an interval-only gate would pass a real regression.
- **Decision.** A gated metric fails on (1) a hard gate below 100% (escalation, prompt injection, forbidden
  promises), (2) a floor, (3) a drop below the baseline's 95% interval, or (4) any stable flip: a case that passed in
  every baseline run and fails in every candidate run. A case that only sometimes fails is flaky, not a flip.
- **Tradeoff.** A single real flip fails the build, which on a model metric can occasionally be noise; the message
  names the case so a person can look.
- **Result.** Project 2's own pre-release dev run fails the gate with 7 named reasons (for example fact grounding
  100% → 88%, cases E07, E16, E24, E26, E30), while the published runs pass.

## 8. Development runs are kept as "history", not as candidates

- **Context.** Project 2's dev runs and Project 1's model comparison are real recordings, but they don't speak for
  the shipped version.
- **Decision.** Run kinds: baseline, candidate, history, demo. The Overview shows the newest gated candidate, or the
  baseline; history and demo runs appear only on "Runs over time".
- **Tradeoff.** One more field to keep right.
- **Result.** The first dashboard draft showed Project 2's dev run as current; that can't happen now
  (`tests/test_dashboard.py`).

## 9. Project 2's promise detector misread a Project 1 policy description

- **Context.** Running Project 2's forbidden-promise detector on Project 1's answers flagged q26 in all three runs:
  "Platinum members receive one free breakfast buffet per guest per day [1]." The detector was written for guest
  drafts, where "free breakfast" is an offer; Project 1 answers staff and quotes the documents.
- **Decision.** For Project 1, a cited sentence with no first-person commitment is a policy description, not a
  promise. Commitments ("I'll waive the fee", "you'll get a free upgrade") are still flagged, cited or not.
- **Tradeoff.** An uncited offer phrased as a description would still be flagged (good); a cited sentence that
  offers something without a commitment verb would pass (accepted: Project 1 can't grant anything).
- **Result.** No forbidden promises 150/153 → 153/153 on Project 1's published run; both directions are unit-tested.

## 10. Request coverage is pass/fail per case in the harness

- **Context.** Project 2 reports the mean share of requests found; intervals and flips need a pass/fail per case.
- **Decision.** A case passes when every labelled request is found.
- **Tradeoff.** Stricter than Project 2's number on partial misses.
- **Result.** Identical on the final run (100%); the dev run shows 92% under both definitions.

## 11. Calibration sample: stratified, blind, seeded

- **Context.** Most outputs are good, so a random sample of 40 would contain almost no failures and kappa would be
  meaningless.
- **Decision.** 40 items: 20 per project; 7 completeness, 7 tone and 6 clarity per project; about half from outputs a
  deterministic metric flagged (Project 2's dev runs, Project 1's Haiku 4.5 comparison). Only model-written text
  (no templates); each case once; seed 2026. The labeling page never shows a metric or the judge's verdict.
- **Tradeoff.** Stratifying by flags over-represents failures, so precision and recall describe this sample, not
  production traffic; Project 1 had only two flagged cases to draw from.
- **Result.** `labels/items.jsonl`; the test suite checks it equals a fresh sample.

## 12. The dashboard is read-only, so it has no admin page or request log

- **Context.** Projects 1 and 2 log requests and have an owner Admin page because visitors type text and every
  request costs money.
- **Decision.** This dashboard accepts no text, calls no API and holds no secrets; it only reads saved files.
- **Tradeoff.** Nothing to monitor beyond Streamlit's own logs.
- **Result.** No secrets are configured on Streamlit Cloud for this app.
