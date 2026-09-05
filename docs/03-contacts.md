# 3. Contacts

One decision-maker per company. Never two people at the same account.

## A contact is a claim with a timestamp, not a fact

An audit of 936 stored contacts found **41% had left the company.** Not wrong
when recorded. Wrong now.

Every system that treats a contact list as durable will quietly send a large
fraction of its volume to nobody, and will read the resulting silence as a copy
problem. It is not a copy problem.

## Who to write to

In order of preference:

1. the sales leader who owns the number
2. the founder or CEO, at companies small enough that they are in the room
3. the SDR or BDR leader
4. a sales director

Under about 100 staff the founder *is* the sales leader, so seniority is cheaper
to reach than the org chart suggests. Above about 500, the most senior person a
data provider lists is usually the group CEO, who is a useless target. Enriching
"the most senior person at this domain" is a good way to spend money on
guaranteed non-answers.

## Verification, and its hard ceiling

Two different questions:

| Question | Answerable? |
|---|---|
| Has this person left? | No. Not from outside. |
| Will this address accept mail? | Partly. |

MX-checking proves the *domain* receives mail. Almost every live company does, so
it discriminates almost nothing. The mailbox needs an SMTP RCPT probe on port 25,
and even that only resolves about half a typical list: most Google Workspace
tenants accept every RCPT and prove nothing, while Microsoft 365 and self-hosted
servers usually answer honestly.

For the unverifiable remainder, **the ramp is the verifier.** Send them early in
small tranches and let the circuit breaker in
[`src/guards.py`](../src/guards.py) stop the batch after roughly one bounce in
twenty-five. A few bounces cost less than a data subscription at low volume.

## On not publishing the finder

This repository ships an MX check and nothing else. Sourcing addresses is the
part with real legal and ethical weight, it is specific to whichever provider you
pay, and a working list-validation tool helps the wrong people most.
