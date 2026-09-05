# Market profiles

One JSON file per target market. Everything vertical-specific lives here so that
nothing in `src/` names an industry, a competitor or a product.

| Profile | Market | Buyer |
|---|---|---|
| `observability.json` | APM / observability sold to engineering teams | VP Engineering, Director of Platform, SRE lead |
| `security.json` | Cybersecurity product vendors | CRO, VP Sales, founder at vendors under ~300 staff |

Two very different markets, identical code. That is the point of the directory:
one profile would prove nothing about generality, which is why
`test_at_least_two_markets_ship` exists.

## Fields

| Field | What it does |
|---|---|
| `market`, `buyer`, `notes` | Documentation. `notes` is where the market's own rules go. |
| `product.mechanism` | Three sentences stating **mechanism, not benefit**. Must contain `{product}`; the name is injected with `--product`. |
| `size_band`, `size_unit` | Below the floor there is no budget; above the ceiling it is an enterprise motion with a procurement cycle. |
| `disqualify` | Checked first and ends the decision. Competitors, agencies, resellers, anyone with no relevant org. |
| `scale_signal` | Evidence they have the problem at a size worth paying to solve. |
| `triggers` | Evidence they are unhappy **now**. `tier` sets priority; `implies_scale` lets a strong trigger satisfy `scale_signal` on its own. |
| `segments` | `[name, regex]`, **most specific first** — first match wins. |
| `angles` | Exactly three subject lines per segment. |

## Rules the loader enforces

`src/profile.py` validates at load and refuses a broken profile rather than
failing halfway through a send:

- every segment has **exactly three** distinct angles — the subject takes one and
  the body gives the other two away, so two or four degrades every email silently
- every regex compiles
- every trigger has a `tier` and a `why`
- every `mechanism` line contains `{product}`
- `size_band` is not inverted
- no duplicate segment names

## Writing a good one

**Order segments most-specific first.** `segment()` returns the first match, so a
broad pattern placed early swallows the narrow ones. The segment picks the
subject line, so a misfiled account gets an email written for someone else's
problem — worse than sending nothing.

**Watch word boundaries.** `\bmicroservice\b` does not match "microservices".
Write `microservices?`. This bug rejected three good accounts in the sample data.

**Triggers are dated, signals are not.** "Runs Kubernetes" is true for years.
"Posted an SRE role naming Datadog" is true this month, and that is what makes it
worth ranking on.

**Set `implies_scale` only where the trigger really proves scale.** A company
emitting OTLP demonstrably produces telemetry. A company hiring one DevOps
contractor does not.

**Angles name the reader's problem, never your product.** If a line would read
the same in a competitor's email, it is a category description, not an angle.
