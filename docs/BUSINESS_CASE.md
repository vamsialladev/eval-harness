# Business case (a projection)

Simulated engagement for a fictional hotel group. **Nothing here is a measured saving.** The API cost of a run is
measured (reports in this repo); every other number is an assumption, stated with its reason, and shown as a range.
Calculator: `python scripts/business_case.py --scenarios`.

## The problem in business terms
The hotel group now runs two AI assistants: staff policy answers (Project 1) and guest email drafts (Project 2).
Each gets changed: a cheaper model, a new prompt, a retrieval setting, new documents. Without a shared, automatic
check, every change means an engineer re-running evals by hand, or not at all. A quality drop that reaches the front
desk costs money: a wrong fee quoted, a comp a manager has to approve after the fact, a missed escalation.

## Assumptions (base case) and why

| Assumption | Base | Why |
|---|---|---|
| Assistants | 2 | Projects 1 and 2 |
| Changes per assistant per month | 4 | Prompts, models, retrieval, dependencies (Dependabot alone opens several a month) |
| Hours to evaluate a change by hand | 3.0 | Run evals for both projects, read outputs, compare with last time |
| Hours with the harness | 0.5 | Read the CI result and any flipped cases |
| Engineer cost per hour | $90 | Loaded cost, mid-range |
| Regressions that would ship unnoticed per year | 4 | One a quarter across two assistants |
| Share the gates catch | 75% | The demo regression was caught; some drops (tone, new topics) aren't gated |
| Cost of a shipped regression | $3,000 | Staff time, guest recovery, manager escalations, rework |
| Live runs per month | 2 | Full re-runs of both projects |
| API cost per full live run | $0.40 | Measured: this project's live runs of both projects (README, API spend) |
| Maintenance per month | 4 h | New cases, label refreshes, rubric reviews |

## Projected results (per year)

| | Pessimistic | Base | Optimistic |
|---|---|---|---|
| Engineer hours saved | 72 | 240 | 504 |
| Value of time saved | $6,480 | $21,600 | $45,360 |
| Regressions avoided (value) | $1,500 | $9,000 | $25,500 |
| API cost | -$10 | -$10 | -$10 |
| Maintenance | -$6,480 | -$4,320 | -$3,240 |
| **Net value** | **$1,490** | **$26,270** | **$67,610** |

## Sensitivity
- **Changes per month** drives most of the value: at 2 a month the harness barely pays for its upkeep.
- **Cost of a regression** matters only in proportion to how many would ship; the honest unknown is the base rate.
- **API cost is negligible** at these volumes (Claude Haiku 5.5, $0.10 / $0.50 per million tokens).

## Value not in the numbers
- A shared definition of "good" for both assistants, which the hotel's team can read.
- Faster, safer model upgrades: a cheaper model can be tried on a branch and judged in minutes.
- An audit trail: every published number re-scores from a saved run in CI.

## Pilot plan
1. Month 1: connect both projects' CI (done in this project), run the gates on every change.
2. Month 2: add 30 held-out cases written by front-desk staff who haven't seen the code; collect a second labeler's
   labels for the judge.
3. Month 3: review: changes caught, false alarms, hours spent.

## KPIs with go / no-go criteria

| KPI | Go | No-go |
|---|---|---|
| False alarms (gate fails on a change that was fine) | ≤ 1 per month | ≥ 3 per month |
| Regressions caught before release | ≥ 1 in the pilot, or a seeded one caught | A known regression passes |
| Engineer time per change | ≤ 1 hour | Unchanged from manual |
| Judge metrics trusted (kappa ≥ 0.6) | At least one, on fresh labels | None after two rubric versions |

## Risks
- **Overfitting the gates:** cases written by the builder flatter the system; held-out cases from staff fix this.
- **A judge that agrees with itself, not people:** it is never a gate unless calibrated, and calibration is redone
  on fresh labels.
- **Flaky model metrics:** stable-flip rules and intervals keep noise from blocking releases; repeated runs measure it.
