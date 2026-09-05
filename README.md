# Outbound engine

How a cold email campaign to B2B software vendors actually gets built, from a
raw list of company names to a message landing in one person's inbox.

This is the working method behind roughly 570 researched prospects and 560+ sent
emails, written out as runnable code. It is a **reference implementation, not a
product**: the sample data is synthetic, no credentials or real contacts are in
the repository, and the sending step is a dry run by default.

The interesting part is not the sending. It is everything that has to be true
before a send is allowed to happen.

---

## The pipeline

```
  raw company names
        |
   [1] sourcing          merge every source, dedupe on domain
        |
   [2] qualification     is this a product vendor, or a reseller wearing the words?
        |
   [3] contacts          one decision-maker per company, verified in seat
        |
   [4] copy              subject and body matched to what the company sells
        |
   [5] deliverability    SPF, DKIM, DMARC pass before anything goes out
        |
   [6] sending           ramp, daily cap, blocklist, typed confirmation
        |
   [7] measurement       one log, per-identity, resume-safe
        v
     one inbox
```

Each stage throws work away. That is the point: the funnel below is from a real
run, and the ratio that matters is the last one.

| Stage | In | Out | Why the drop |
|---|---:|---:|---|
| Sourced | 2,305 | 2,305 | every list, deduped on domain |
| Classified as security vendors | 2,305 | 1,219 | IT services, resellers and media removed |
| Passed the product gate | 1,219 | 571 | sells a product, not an implementation of someone else's |
| Contact confirmed in seat | 936 audited | 553 | **41% of stored contacts had left the company** |
| Sent | 571 | 542 | blocked countries, bounces, suppression |

That 41% figure is the one that changes how you build these systems. A contact
list is a perishable good. Anything that treats it as a fact rather than a claim
with a timestamp will quietly send half its volume into the void.

---

## What each stage does

| # | Doc | Code |
|---|---|---|
| 1 | [Sourcing](docs/01-sourcing.md) | — |
| 2 | [Qualification](docs/02-qualification.md) | [`src/classify.py`](src/classify.py) |
| 3 | [Contacts](docs/03-contacts.md) | [`src/verify.py`](src/verify.py) |
| 4 | [Copy](docs/04-copy.md) | [`src/angles.py`](src/angles.py), [`src/compose.py`](src/compose.py) |
| 5 | [Deliverability](docs/05-deliverability.md) | [`src/verify.py`](src/verify.py) |
| 6 | [Sending](docs/06-sending.md) | [`src/guards.py`](src/guards.py) |
| 7 | [Measurement](docs/07-measurement.md) | — |

---

## Run it

No dependencies outside the standard library. Python 3.9+.

```bash
git clone https://github.com/<you>/outbound-engine
cd outbound-engine

python3 -m src.classify data/sample_companies.csv   # the product gate, with reasons
python3 -m src.compose  data/sample_companies.csv   # the emails it would send
python3 -m src.guards   --demo                      # every guard, and what trips it
python3 -m src.verify   --mx example.com            # does this domain accept mail

python3 -m unittest discover tests -v
```

`src.compose` prints to stdout. Nothing in this repository can send an email;
there is no SMTP client and no credential loading anywhere in it.

---

## The three ideas worth stealing

**1. The gate runs in a fixed order, and ties are marked, not guessed.**
Hard-reject reseller and training language first, then require a product signal,
then require the security signal. A company showing *both* product and services
language is not guessed at, it is flagged `CHECK` for a human. Rapid7 sells
products *and* managed services; a pure reseller has the services words and
nothing else. One ordered pass separates them; a bag of keywords does not.

**2. Copy is matched to the product category, and the match is the argument.**
A vulnerability-management vendor and an identity vendor sell to different people
with different problems. The subject line is written for the *recipient's buyer*,
not for the recipient, which is what makes it evidence of ability rather than a
claim of it. Fourteen categories, three angles each, in
[`src/angles.py`](src/angles.py).

**3. The guards are code, not discipline.**
Every safety property is enforced by the program and cannot be met by intending
to meet it:

- a **true per-day cap** that reads back what was already sent today, so a second
  run of the same command sends the remainder or nothing
- a **ramp** that ceilings volume by day number from that sender's first ever
  send, which `--daily-cap` can only lower
- **hours and weekday** limits
- a **four-layer blocklist** that fails closed and is re-checked immediately
  before every individual send, not just at startup
- **identity binding**: the OAuth token names its own mailbox and the program
  refuses to run if that disagrees with the From header
- a **typed confirmation** before any real send

This list exists because on one day a campaign sent 470 emails against a plan of
35, and 297 of them went out between midnight and 05:00. The cap was per-run
instead of per-day, so five invocations meant five caps. Nothing was malicious
and nobody was careless. The cap was simply advisory, and advisory limits are not
limits. See [Sending](docs/06-sending.md).

---

## What is deliberately not here

No contact data, no API keys, no OAuth tokens, no send log, no company list.
`data/sample_companies.csv` is invented: the domains are RFC 2606 reserved names
that cannot resolve to a real business.

No scraper and no enrichment client either. Sourcing contacts is the part with
the real legal and ethical weight, it is specific to whichever provider you pay,
and publishing a working one helps the wrong people most. Stage 3 documents what
to check about a contact and how to verify a mailbox exists. It does not help you
find one.

---

## On consent

Cold email to a business address about that business is lawful in most places and
regulated in all of them. GDPR needs a legitimate interest assessment and a real
opt-out. CAN-SPAM needs an accurate From, a physical address and honoured
unsubscribes. PECR and CASL are stricter and CASL wants consent up front.

The engineering that follows from that is unglamorous and load-bearing:
suppression is permanent and checked before every send, replies suppress the
whole domain rather than the one address, and there is one log so nobody is
contacted twice by two different campaigns.

MIT licensed.
