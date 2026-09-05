# 1. Sourcing

Merge every list you have, dedupe on **registered domain**, keep the provenance.

## Dedupe on domain, not company name

"Rapid7", "Rapid7 Inc", "Rapid7, Inc." and "rapid 7" are four rows and one
company. Names are written by humans and vary without limit; the domain is the
only stable key. Normalise it first: lowercase, strip `www.`, strip the path,
resolve the obvious country variants you know about.

This alone collapsed 2,305 rows to a working set with no manual review.

## Keep provenance on every row

Record which source each row came from and when. When a segment later turns out
to be full of resellers, you want to remove that *source*, not re-litigate 2,000
rows one at a time. Sources rot at different rates and you will want to weight
them differently later.

## Never write back to a source

Source files are read-only. Every derived artefact goes in its own directory.
This sounds pedantic until the day a script with a bug rewrites the only copy of
a list somebody spent a month building.

## What comes out

A single table: domain, company name, every source that mentioned it, first seen.
No judgement yet. Judgement is stage 2, and keeping it separate means you can
re-run the gate with a better gate without re-doing the merge.
