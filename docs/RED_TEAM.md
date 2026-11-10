# Red team

**Not applicable, on purpose.** The live dashboard has no text input, makes no model calls, holds no secrets and
writes no logs: it only reads the saved reports bundled with the repo (decision 12). There's nothing for a prompt
injection or a data request to reach.

What it does have, and how it's covered:

| Surface | Risk | Defence |
|---|---|---|
| URL query parameters | A crafted link | Only `source=keepawake` is read (the shared `bots` check); every other parameter is ignored |
| Saved reports | A report file carrying script or markup | Every value is escaped before display (`views/components.esc`); reports are written by this repo's own runner and reviewed in PRs |
| The judge (CLI, not the dashboard) | Planted text in a reply steering the grade | The judge's rubric treats replies as data; nothing is gated on the judge (it hasn't agreed with human labels well enough, kappa 0.29) |

The red-team suites that matter live in the apps this harness measures: hotel-ops-assistant, guest-request-agent,
resort-activities-concierge, hotel-tools-mcp, hotel-ops-analytics-agent and fde-account-research-agent each run the
shared corpus from [hotel-ai-platform](https://github.com/vamsialladev/hotel-ai-platform) plus their own cases in CI.
