# 7. Measurement

## One log, and everything reads it

A single append-only record of every send: address, company, subject, timestamp,
and which identity sent it. It is simultaneously the deduplication index, the
daily cap, the ramp counter, the resume point and the audit trail. Five features
from one file, which is why it must never be reconstructed from anything else.

## The trap: shared log, multiple identities

When a second sender started using the same log, every prospect the *first*
campaign had ever emailed was skipped as "already handled" — even though the
second sender had never written to them.

The fix is that "handled" is a **per-identity** question. Each entry records
which identity sent it, and each campaign counts only its own. This looks like a
small change and is not: it touches the exact failsafe that stops double-sends,
so it deserves a test rather than a careful read.

A related subtlety: an address that failed once and later succeeded is not dead.
Treat the latest outcome as the truth, not the first.

## What to measure

| Metric | Why |
|---|---|
| Bounce rate | list quality, and the circuit breaker's input |
| Reply rate | the only number that matters. 1-2% is a normal baseline for genuinely cold B2B |
| Positive reply rate | reply rate alone counts "unsubscribe" as success |
| Replies per category | tells you which angles work, which is how the copy improves |

## Silence is not data

Zero replies has at least four causes: authentication failure, dead addresses,
wrong audience, bad copy. They are indistinguishable from the outside, and they
are listed in the order you should rule them out. Rewriting copy is the most fun
and the least likely to be the problem, so it goes last.

This is the practical argument for doing [deliverability](05-deliverability.md)
first: until SPF, DKIM and DMARC pass, silence carries no information at all.

## Reply handling

Replies suppress the whole domain immediately, permanently, before the next
batch. A follow-up sent to someone who already answered undoes whatever the first
email earned.
