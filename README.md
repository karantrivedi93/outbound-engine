# Outbound engine

A working outbound system for a developer-tools company: from a raw list of
companies to one email in one engineering leader's inbox.

**Configured for [SigNoz](https://signoz.io) — OpenTelemetry-native observability
sold to engineering teams.** The engine is not SigNoz-specific; the product
appears in exactly one block in `src/compose.py` and the buyer segments live in
`src/angles.py`. Both are swappable. It ships pointed at SigNoz because that is
the market I built this configuration for.

Standard library only. `data/` is synthetic. Nothing here can send an email.

---

## The pipeline

```
  companies + public signal
        |
   [1] sourcing          merge, dedupe on domain, keep provenance
        |
   [2] qualification     do they have the problem, and can they buy?
        |                -> PASS / CHECK (nurture) / REJECT, each with evidence
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
python3 -m src.classify data/sample_companies.csv   # the ranked target list
python3 -m src.compose  data/sample_companies.csv   # the emails, tier 1 first
python3 -m src.guards   --demo                      # every guard, and what trips it
python3 -m unittest discover tests -v               # 29 tests
```

---

## The idea the whole thing rests on

**A list is not a target list until it is ordered.**

Filtering answers "could I email this company". Ranking answers "who do I email
on Monday morning", and only the second one is the job. Given 400 plausible
accounts and no order, you work them alphabetically, which means working them by
accident.

So qualification returns a **tier**, and the tier comes from how warm the trigger
is — never from how big the company is.

| Trigger | Tier | Why |
|---|:--:|---|
| **OpenTelemetry in production** | 1 | They already did the expensive half of the migration. Instrumentation is portable; the backend is now a choice rather than a rebuild. |
| **Incumbent named** (Datadog, New Relic, Dynatrace, Splunk) | 1 | There is a bill, an owner and a renewal date. Displacement is harder than greenfield, but the budget already exists. |
| **Hiring SRE / platform** | 2 | Someone signed off on reliability headcount. Budget and pain exist; the specific complaint is not visible yet. |
| Real infrastructure, no trigger | 3 | Nurture. **Not a reject** — rejecting deletes them permanently, and they are simply not this week's work. |

A 40-engineer company already running OTel is a better Monday morning than a
900-engineer company with nothing but a job post. Sorting by headcount gets that
exactly backwards, which is what most target lists do.

---

## Writing to engineers

Selling to engineers is not selling with fewer adjectives. It is a different
burden of proof: a VP Engineering can check every claim you make against a system
they know better than you do. So the only durable move is to say one specific,
checkable, true thing and let them verify it.

What [`src/compose.py`](src/compose.py) enforces, with a test behind each:

- **One observation, about their system, not the product.**
  *"Billed per host for pods that live 40 seconds"* is checkable.
- **No adjectives about the product.** Nothing is powerful, seamless or
  best-in-class. `test_no_marketing_adjectives_survive` fails the build on eight
  of them.
- **Mechanism, not benefit.** *"Reads OTLP directly, no agent in your code, so
  leaving later costs a config change"* is a fact someone can check. "Unified
  observability" is a claim, and a technical reader hears the second one as an
  admission that there was nothing checkable to say.
- **Never claim open source is cheaper.** It is a different cost structure.
  Anyone who runs infrastructure knows self-hosting costs engineer-hours, and
  overclaiming loses them on line one.
- **Give away the two angles the subject did not use.** Costs nothing, and makes
  the email useful to someone who never replies.

Ten buyer segments, three angles each, in [`src/angles.py`](src/angles.py).

---

## The guards, and the day that caused them

Every safety property is enforced by the program, because a limit that depends on
the operator remembering is not a limit, it is a preference.

This is not hypothetical. One day a campaign sent **470 emails against a plan of
35**, 297 of them between midnight and 05:00, to a list that was almost entirely
US-based. `--daily-cap 35` was a **per-run** cap with no memory, so five
invocations meant five caps. The sender had been writing a timestamp on every
send since day one and nothing had ever read it back. Nobody was careless; the
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

`python3 -m src.guards --demo` prints all of it.

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
account in the file — for never using the word "microservices". Anyone emitting
OTLP has already proved they produce telemetry. Requiring them to also say the
magic word tests their copywriting, not their architecture. Triggers are now
found first and two of them satisfy the scale test on their own.

**Most-specific patterns must be tried first.** `segment()` returns the first
match, so a general pattern placed early swallows the specific ones. The category
chooses the subject line, so a misfiled company gets an email written for someone
else's problem, which is worse than sending nothing.

---

## What is deliberately absent

**No contact-finding code and no SMTP client.** Nothing here can build a list or
send an email. Sourcing addresses is the part with real legal weight, it is
specific to whichever provider you pay, and publishing a working list-validation
tool helps the wrong people most. Stage 3 documents what to verify and how to
check a domain accepts mail. It does not help you find an address.

**No real data.** No contacts, no credentials, no send log. The sample domains
are RFC 2606 reserved names that cannot resolve to a real business, and
`.gitignore` blocks `.env`, tokens and any `*contacts*.csv` as a backstop.

## On consent

Cold email to a business address about that business is lawful in most places and
regulated in all of them. GDPR wants a legitimate interest assessment and a real
opt-out; CAN-SPAM wants an accurate From, a physical address and honoured
unsubscribes; CASL wants consent up front.

The engineering that follows is unglamorous and load-bearing: suppression is
permanent and checked before every send, a reply suppresses the whole domain, and
there is one log so nobody is contacted twice by two campaigns.

MIT licensed.
