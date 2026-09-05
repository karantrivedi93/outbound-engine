# Outbound engine

A working cold-outbound system for B2B software: from a raw list of companies to
one email in one buyer's inbox.

**The market is a config file.** Everything vertical-specific — who to
disqualify, what counts as a buying trigger, which pain to lead with, the subject
lines — lives in `profiles/*.json`. No module names an industry, a competitor or
a product. Two very different markets ship as worked examples and run through
identical code:

```bash
python3 -m src.classify --profile observability   # APM sold to engineering teams
python3 -m src.classify data/sample_security.csv --profile security
```

Standard library only, Python 3.9+. `data/` is synthetic. **Nothing here can send
an email or build a list.**

---

## The pipeline

```
  companies + public signal
        |
   [1] sourcing          merge, dedupe on domain, keep the evidence
        |
   [2] qualification     do they have the problem, and can they buy?
        |                -> PASS / CHECK (nurture) / REJECT, each with its evidence
   [3] prioritisation    tier by how warm the trigger is, never by company size
        |
   [4] copy              one checkable observation about THEIR system
        |
   [5] deliverability    SPF, DKIM, DMARC pass before anything goes out
        |
   [6] sending           ramp, daily cap, blocklist, typed confirmation
        |
   [7] measurement       one log; per-identity; resume-safe
        v
     one inbox
```

```bash
python3 -m src.profile                              # what markets are configured
python3 -m src.classify --profile observability     # the ranked target list
python3 -m src.compose  --profile observability --product "Acme APM"
python3 -m src.guards   --demo                      # every guard, and what trips it
python3 -m unittest discover tests -v               # 35 tests
```

---

## The idea the whole thing rests on

**A list is not a target list until it is ordered.**

Filtering answers *could I email this company*. Ranking answers *who do I email
on Monday morning*, and only the second one is the job. Given 400 plausible
accounts and no order, you work them alphabetically, which means working them by
accident.

So qualification returns a **tier**, and the tier comes from how warm the trigger
is — never from how big the company is.

| Trigger (observability profile) | Tier | Why |
|---|:--:|---|
| **OpenTelemetry in production** | 1 | They already did the expensive half of the migration. Instrumentation is portable; the backend is now a choice rather than a rebuild. |
| **Incumbent named** | 1 | There is a bill, an owner and a renewal date. Harder than greenfield, but the budget exists. |
| **Hiring SRE / platform** | 2 | Someone signed off on reliability headcount. Budget and pain exist; the complaint is not visible yet. |
| Real infrastructure, no trigger | 3 | Nurture. **Not a reject** — rejecting deletes them permanently, and they are simply not this week's work. |

A 40-person company with a tier-1 trigger is a better Monday morning than a
900-person company showing nothing but a job post. Sorting by headcount gets that
backwards, which is what most target lists do.

**A gate that cannot say "not yet" will say it as a permanent no.**

---

## Writing to a technical buyer

Not "the same email with fewer adjectives" — a different burden of proof. A VP
Engineering can check every claim you make against a system they know better than
you do. So: say one specific, checkable, true thing about *their* system, and let
them verify it.

What `src/compose.py` enforces, each with a test behind it:

- **One observation, about their system.** *"Billed per host for pods that live
  40 seconds"* is checkable against their own invoice.
- **No adjectives about the product.** `test_no_marketing_adjectives_survive`
  fails the build on eight of them, across every segment of every profile,
  because this is the failure that creeps back in.
- **Mechanism, not benefit.** *"Reads OTLP directly, no agent in your code, so
  leaving later costs a config change"* is a fact with consequences the reader
  works out themselves. "Unified observability" is a claim, and a technical
  reader hears it as an admission there was nothing checkable to say.
- **Never claim open source is cheaper.** It is a different cost structure, and
  anyone who runs infrastructure has already priced the engineer-hours.
- **Give away the two angles the subject did not use.** Costs nothing, and makes
  the email useful to someone who never replies — which is most people.

No merge fields. There is no *"I saw you raised a Series B"* anywhere in this.
What is personal is the **argument**: the segment comes from public evidence
about their stack, and the subject comes from the segment. Much harder to fake
than a merge field, and much harder to automate badly.

---

## The guards, and the day that caused them

Every safety property is enforced by the program, because **a limit that depends
on the operator remembering is not a limit, it is a preference.**

Not hypothetical. One day a campaign sent **470 emails against a plan of 35**,
297 of them between midnight and 05:00, to a list that was almost entirely
US-based. `--daily-cap 35` was a **per-run** cap with no memory, so five
invocations meant five caps. The sender had written a timestamp on every send
since day one and nothing had ever read it back. Nobody was careless; the
operator's intent was correct every single time.

- **True per-day cap** — reads the log back, so a second run of the same command
  sends the remainder or nothing
- **Enforced ramp** — ceiling by day number from that sender's first ever send;
  `--daily-cap` may only lower it
- **Four-layer blocklist, failing closed** — anything unparseable is blocked, and
  layer 4 re-checks immediately before each individual send
- **Suppression by domain, not address** — someone who asked to be left alone did
  not mean "email my colleague instead"
- **Identity binding** — the credential names its own mailbox; the program
  refuses to run if that disagrees with the From header
- **Typed confirmation** — subject and word count printed, literal `YES`
  required. This exists because 54 emails once went out on the wrong template
- **Circuit breaker** — stops at a 4% failure rate; a batch of dead addresses
  halts itself

---

## Adding a market

Write one JSON file in `profiles/`. `src/profile.py` validates it at load and
**refuses to return a broken profile** rather than failing halfway through a
send — a segment with no angles, a segment with two, a bad regex, a trigger with
no tier. All four have bitten a real run, and all four are cheap here and
expensive later.

```json
{
  "market": "...", "buyer": "...",
  "product":  {"mechanism": ["{product} does X, so Y.", "...", "..."]},
  "size_band": [15, 2000], "size_unit": "engineers",
  "disqualify":   {"competitor": "regex"},
  "scale_signal": "regex",
  "triggers": [{"name": "...", "tier": 1, "pattern": "regex",
                "why": "...", "implies_scale": true}],
  "segments": [["Segment name", "regex"]],
  "angles":   {"Segment name": ["three", "subject", "lines"]}
}
```

The test suite runs over **every** profile found, so adding a market gets the
same checks for free.

---

## Bugs worth reading, all found building this

Kept in the code as comments, because the reasoning is the useful part.

**A word boundary cost three good accounts.** `\bmicroservice\b` does not match
"microservices", and `\bcontainer\b` does not match "containers" — which is how
every engineering blog on earth writes them. Three of twelve sample companies
were rejected for owning infrastructure they had described in the plural.

**Ordering a gate wrong rejects your best account.** The qualifier demanded an
architecture keyword *before* looking for triggers, and threw out a company
running OpenTelemetry collectors and migrating off New Relic — the warmest
account in the file — for never saying "microservices". Anyone emitting OTLP has
already proved they produce telemetry; requiring the magic word too tests their
copywriting, not their architecture. Triggers are now found first, and a trigger
flagged `implies_scale` satisfies the scale test on its own.

**Most-specific patterns must be tried first.** `segment()` returns the first
match, so a general pattern placed early swallows the specific ones. The segment
chooses the subject line, so a misfiled account gets an email written for
somebody else's problem — worse than sending nothing.

All three are silent, confident false negatives. Nothing in the output tells you
they happened, which is why `tests/` asserts known answers on every change.

---

## What is deliberately absent

**No contact-finding code and no SMTP client.** Sourcing addresses is the part
with real legal weight, it is specific to whichever provider you pay, and a
working list-validation tool helps the wrong people most. Stage 3 documents what
to verify and how to check a domain accepts mail. It does not help you find an
address.

**No real data.** No contacts, no credentials, no send log. Sample domains are
RFC 2606 reserved names that cannot resolve to a real business, and `.gitignore`
blocks `.env`, tokens and any `*contacts*.csv` as a backstop.

## On consent

Cold email to a business address about that business is lawful in most places and
regulated in all of them. GDPR wants a legitimate interest assessment and a real
opt-out; CAN-SPAM wants an accurate From, a physical address and honoured
unsubscribes; CASL wants consent up front.

The engineering that follows is unglamorous and load-bearing: suppression is
permanent and checked before every send, a reply suppresses the whole domain, and
there is one log so nobody is contacted twice by two campaigns.

MIT licensed.
