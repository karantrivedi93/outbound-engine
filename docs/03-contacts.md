# 3. Contacts

One person per company. Never two people at the same account in the same week.

## A contact is a claim with a timestamp, not a fact

An audit of 936 stored contacts found **41% had left the company.** Not wrong
when recorded. Wrong now.

Any system that treats a contact list as durable will quietly send a large share
of its volume to nobody, then read the resulting silence as a copy problem. It is
not a copy problem, and no amount of rewriting the subject line will fix it.

## Who to write to at an engineering org

Match the seniority to the size, not to the title you wish you could reach:

| Company size | Write to | Why |
|---|---|---|
| Under ~50 engineers | CTO or founding engineer | They chose the stack and they see the bill |
| 50 to 300 | VP Engineering, Director of Platform | Owns both the budget line and the on-call burden |
| 300 to 2,000 | SRE lead, observability owner, platform lead | The problem is somebody's actual job title by now |
| Over 2,000 | someone specific, via a warm path | Cold email to a title at this size is a lottery ticket |

Two things that are true of this buyer and not of most:

**They will read the technical claim more carefully than the ask.** Get the
mechanism right and a mediocre call-to-action still works. Get the mechanism
wrong and nothing rescues it.

**The person with the pain is often not the person with the budget, and both are
in engineering.** An SRE feels it daily; a VP signs. Writing to the SRE with a
procurement pitch, or to the VP with a config detail, misses in both directions.

## Verification, and its hard ceiling

Two different questions:

| Question | Answerable? |
|---|---|
| Has this person left? | No. Not from outside. |
| Will this address accept mail? | Partly. |

MX-checking proves the *domain* receives mail. Almost every live company does, so
it discriminates almost nothing. The individual mailbox needs an SMTP RCPT probe
on port 25, and even that resolves only about half of a typical list: most Google
Workspace tenants accept every RCPT and so prove nothing, while Microsoft 365 and
self-hosted servers usually answer honestly.

For the unverifiable remainder, **the ramp is the verifier.** Send them early in
small tranches and let the 4% circuit breaker in
[`src/guards.py`](../src/guards.py) stop the batch after roughly one bounce in
twenty-five. A few bounces cost less than a data subscription at this volume.

## On not publishing the finder

This repository ships an MX check and nothing else. Sourcing addresses is the
part with real legal and ethical weight, it is specific to whichever provider you
pay, and a working list-validation tool helps the wrong people most.
