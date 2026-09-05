# 1. Sourcing

For a developer tool, the list is not the hard part. **The signal is.**

Any provider will sell you ten thousand companies with 50 to 500 engineers. That
list is worthless on its own, because it tells you nothing about whether anyone
there is currently unhappy. What makes an account workable is public evidence
that the problem exists *right now*, and that evidence is mostly free.

## Where the signal actually lives

| Source | What it tells you |
|---|---|
| **Job postings** | The single richest source. A Senior SRE post lists the stack by name, often including the incumbent, and its existence proves someone approved headcount for reliability. |
| **Engineering blogs** | "How we cut our observability spend", "Migrating to OpenTelemetry", "Why we left X". A public post is a public admission of the problem, and it is dated. |
| **Conference talks** | Same, plus a named person who is already willing to talk about it. |
| **Public repos and configs** | Collector configs, Helm charts and docker-compose files in public repos show the actual stack rather than the aspirational one. |
| **Status pages and incident write-ups** | A postmortem naming slow diagnosis is a problem statement written by the prospect. |

Every one of these is dated, which is what makes it a *trigger* rather than a
fact. Stage 2 ranks on how warm the trigger is, so the timestamp matters as much
as the content.

## Mechanics that stop you doing it twice

**Dedupe on registered domain, never company name.** "Acme", "Acme Inc",
"Acme, Inc." and "acme labs" are four rows and one company. Names are written by
humans and vary without limit; the domain is the only stable key. Normalise
first: lowercase, strip `www.`, strip the path.

**Keep provenance on every row.** Which source, and when. When a segment turns
out to be full of agencies, you want to remove that *source*, not re-litigate
2,000 rows individually. Sources rot at different rates and you will want to
weight them differently later.

**Never write back to a source.** Source files are read-only; derived artefacts
live in their own directory. This sounds pedantic until a script with a bug
rewrites the only copy of a list someone spent a month building.

**Record the evidence, not just the verdict.** Store the sentence that made you
believe the trigger, not a boolean. Six weeks later you will need to know whether
"uses Datadog" came from a job post or from a guess, and a boolean cannot tell
you.

## What comes out

One table: domain, company, engineer count, the evidence text, each source, first
seen. **No judgement yet.** Judgement is stage 2, and keeping the two separate
means you can re-run a better gate over the same evidence without redoing the
collection.

## On scrapers

This repository ships no collector, deliberately. Rate limits, terms of service
and robots directives are real constraints, and a working scraper is the part of
this that is most useful to someone acting in bad faith. Read the terms for each
source, identify yourself honestly, cache aggressively so you fetch each page
once, and treat "this page asked me not to" as a stop rather than a puzzle.
