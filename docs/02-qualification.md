# 2. Qualification and prioritisation

**Code: [`src/classify.py`](../src/classify.py)**

A list is not a target list until it is ordered.

Filtering answers *could I email this company*. Ranking answers *who do I email
on Monday morning*, and only the second one is the job. A founding SDR with 400
plausible accounts and no order will work them alphabetically, which is working
them by accident.

## The gate

```
1. disqualify   competitor, agency, or no engineering org at all
2. trigger?     evidence they are unhappy or already moving
3. scale?       do they run something that emits real telemetry
4. size band?   too small has no budget, too large is a different motion
5. rank         tier by how warm the trigger is, never by company size
```

## The three triggers, warmest first

**OpenTelemetry in production.** The strongest signal available. They have
already done the expensive half of a migration: the instrumentation is portable,
so the backend is now a *choice* rather than a rebuild. Everything that normally
makes displacement hard has already been paid for by someone else.

**An incumbent named.** Datadog, New Relic, Dynatrace, Splunk. There is a bill,
an owner and a renewal date. Harder than greenfield, but the budget exists and
you are arguing about allocation rather than creating a line item.

**Hiring SRE or platform.** Someone signed off on reliability headcount, so
budget and pain both exist. The specific tool complaint is not visible yet, which
is why this is tier 2 rather than tier 1.

## Tier is not size

A 40-engineer company already running OTel is a better Monday morning than a
900-engineer company with nothing but a job post. Sorting a target list by
headcount gets this exactly backwards, and most target lists are sorted by
headcount.

Above roughly 2,000 engineers the account is real but the motion is different:
procurement, security review, a committee. That is not a founding SDR's first
touch, so it is marked for later rather than worked now.

## CHECK is not REJECT

A company with real infrastructure and no visible trigger is **nurture**, not a
reject. Rejecting deletes them from the list permanently; they are simply not
this week's work. Re-run the gate when new signal appears — a job post, a
conference talk, an engineering blog on cost — and they become tier 1 or 2
without anyone having to remember they existed.

A gate that cannot say "not yet" will express that as a permanent no.

## Every verdict carries its evidence

`classify()` returns the reasons alongside the verdict, and the CLI prints them.
A ranking nobody can argue with is a ranking nobody will correct.

## Two bugs, both real, both in the code as comments

**A word boundary cost three good accounts.** `\bmicroservice\b` does not match
"microservices". Neither does `\bcontainer\b` match "containers". Three of twelve
sample companies were rejected for owning infrastructure they had described in
the plural.

**Ordering the gate wrong rejected the best account in the file.** The first
version demanded an architecture keyword before looking for triggers, and threw
out a company running OpenTelemetry collectors and migrating off New Relic —
because the description never said "microservices". Anyone emitting OTLP has
already proved they produce telemetry worth paying for. Requiring them to also
say the magic word tests their copywriting, not their architecture.

That second class of bug is the dangerous one: a silent, confident false negative
on exactly the accounts most worth reaching. Nothing in the output tells you it
happened. The only defence is a set of known-answer cases asserted on every
change, which is what `tests/test_guards.py` is.
