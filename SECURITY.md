# Security and Data Privacy

This is a portfolio project: a **simulated client engagement** for a fictional hotel group, with **synthetic**
documents, guests, bookings and emails. The harness evaluates the hotel group's two assistants (Projects 1 and 2).

## Data handled
- **Cases:** the projects' synthetic labelled questions and emails, imported at pinned commits, plus cases added in
  Project 3. Fictional names and `@example.com` addresses only.
- **Recorded outputs (`runs/`):** the assistants' answers and drafts to those synthetic cases, with tool results
  and timings. No visitor data: nothing typed into the live apps is ever recorded here.
- **Human labels (`labels/human-labels.jsonl`, `labels/human-labels-round2.jsonl`):** the owner's pass/fail clicks and optional
  reasons on 70 items in two blind rounds.
- **Sent to the Claude API (judge and live runs only):** the case text, the reply being judged and the rubric. The
  dashboard and CI never call the API.

## The dashboard
Read-only: it accepts no text, makes no API calls, holds no secrets, sets no cookies and adds no analytics. It has
no admin page and no request log because there is nothing to log (docs/DECISIONS.md, decision 12). The labeling page
(`label_app.py`) runs only on the owner's machine and is never deployed.

## Secrets
- `ANTHROPIC_API_KEY` lives only in `.env` (git- and docker-ignored). The live runner passes it to the project's
  process through the environment only; it is never printed, logged, written to a file or recorded.
- Pre-commit blocks private keys. GitHub secret scanning and push protection are on for the repository.
- Before every push: `git ls-files` must not contain `.env`, and the full history is scanned for the Anthropic key
  prefix and for the configured key value itself (zero hits required).
- **Spending limit:** keep a monthly limit in the Anthropic Console. This project's whole API spend is reported in
  the README.

## Risks and mitigations

| Risk | Mitigation | Where |
|---|---|---|
| A quality drop ships silently (prompt, model or retrieval change) | Recorded-mode gates in CI for both projects: hard 100% gates, floors, baseline intervals, stable flips | `src/hoteleval/gates.py`, `.github/workflows/ci.yml` |
| A metric passes for the wrong reason | Every metric has a passing and a failing unit test; the projects' published numbers are reproduced from the same recordings | `tests/test_metrics.py`, `tests/test_reproduce.py` |
| An untrusted LLM judge becomes a gate | A judge metric is trusted only at Cohen's kappa ≥ 0.6 against human labels, and is never listed in `gates.toml` otherwise | `src/hoteleval/calibration.py` |
| Text inside a case or reply instructs the judge ("rate this pass") | Case and reply are wrapped as data in the judge prompt; structured output only (verdict + short reason) | `src/hoteleval/judge.py` |
| A live run modifies a project's checkout | Live runs export the pinned commit with `git archive` into `.work/` | `src/hoteleval/runner.py` |
| Published numbers drift from the code | CI re-scores every saved report and fails on any difference | `scripts/check_reports.py` |
| XSS through recorded text on the dashboard | Every dynamic value is escaped before HTML; outputs are shown in code blocks | `views/components.py` |

## OWASP Top 10 for LLM applications (2025)

The harness calls a model only as a judge and in live runs; the dashboard calls none.

| ID | Risk | How this project handles it |
|---|---|---|
| LLM01 | Prompt injection | Case and reply are wrapped as data in the judge prompt; structured output only (verdict and a short reason); injection cases in both projects are hard 100% gates |
| LLM02 | Sensitive information disclosure | Synthetic cases only; no visitor data is ever recorded; the API key is passed by environment and never written |
| LLM03 | Supply chain | Standard-library core, pinned extras, pip-audit in CI, Dependabot, secret scanning and push protection |
| LLM04 | Data and model poisoning | Cases are imported at pinned commits (`src/hoteleval/pins.py`); CI re-scores every saved report and fails on any difference |
| LLM05 | Improper output handling | Recorded text is escaped before display on the dashboard |
| LLM06 | Excessive agency | The harness has no tools and takes no actions; live runs use a `git archive` export, never the project's checkout |
| LLM07 | System prompt leakage | No secrets in prompts; rubrics are in the repository |
| LLM08 | Vector and embedding weaknesses | Not applicable: the harness indexes nothing; it measures the projects' retrieval |
| LLM09 | Misinformation | Deterministic metrics, each with a passing and a failing test; the judge is never gated until kappa ≥ 0.6 against human labels (it reached 0.29) |
| LLM10 | Unbounded consumption | The judge caches by input hash; live runs are run by hand with prices as flags; the dashboard makes no API calls |

## Reporting a vulnerability
Email vamsialla.dev@gmail.com. Please don't open a public issue for security problems.
