# 5. Deliverability

**Code: [`src/verify.py`](../src/verify.py) (`--notes`)**

Get this right before the first send. Not after the first disappointing week.

## The three records

| | |
|---|---|
| **SPF** | **One record only.** Two is an RFC 7208 PermError and is worse than one wrong record. If it ends in `-all` and your real sender is not listed, that is a hard fail at every receiver, every time. |
| **DKIM** | A published DNS record is **not** the same as signing being switched on. A record with signing disabled is the failure that looks like success. Confirm in the provider console that it says *authenticating*. |
| **DMARC** | Start at `p=none` during warmup, move to `quarantine` once passes are clean. Point `rua` at a mailbox a human actually reads. |

## Verify, don't assume

Send one message to a Gmail address, open **Show original**, and confirm SPF,
DKIM and DMARC all say PASS. Cross-check on mail-tester.com and aim for 9/10.

## What it costs to skip this

A domain whose SPF hard-failed sent two dozen cold emails over three days. Zero
bounces. Zero replies.

That combination is the trap. **A bounce tells you an address is dead. Silence
tells you nothing at all**, and it is indistinguishable from bad copy, a bad
list, or bad timing. Weeks get spent rewriting a subject line when the actual
fault is one DNS record. Authenticate first so that silence becomes evidence.

## A warning about registrars

Some registrars attach an SPF record to a bundled email product and refuse to let
you delete it while that product exists, returning an immutable-record error.
Cancelling the product does not always release the lock. Budget real time for
this, and do not open a two-SPF-record window while retrying: two records is a
PermError, which is strictly worse than the single wrong one you started with.

## Warm the domain

Two to three weeks of real two-way conversation before any cold volume. A new
domain that sends 200 emails on day one has told every receiver exactly what it
is. See the ramp in [Sending](06-sending.md).
