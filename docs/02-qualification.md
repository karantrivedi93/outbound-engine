# 2. Qualification

**Code: [`src/classify.py`](../src/classify.py)**

The question is not "is this company in cybersecurity". It is "does this company
sell a product it built". Those are very different, and the words are identical.

## Why keyword scoring fails

A reseller's website, an IT-services firm's website and a real vendor's website
all use the same nouns. A consultancy says "platform" because it implements one.
A trade magazine says "threat" a hundred times a day. Score the keywords and all
three pass.

## What works: an ordered gate that can say "I don't know"

```
1. hard reject   reseller / distributor / training / media / recruiter
2. product?      must show it ships software of its own
3. security?     must be about security at all
4. tie-break     product AND services language -> CHECK, do not guess
```

Step 4 is the whole design. A vendor with a managed-service arm is
indistinguishable from a reseller by vocabulary alone. Rapid7 sells products
*and* MDR. A pure reseller has the services language and nothing behind it. When
both signals fire, the row is flagged for a human rather than decided by
whichever word list happened to be longer.

A gate that cannot return "I don't know" will express its uncertainty as
confident wrong answers instead, and you will not be able to tell which ones.

## Two bugs from the real thing, both worth knowing

**Acronyms must appear in the security signal.** The first version matched only
spelled-out words, so a company calling itself an "XDR platform" matched nothing
and was rejected for not being a security company. A silent false negative on
exactly the vendors most worth reaching. Anything you use as a category must be
recognisable as a signal too.

**Category patterns must run most-specific first.** `categorise()` returns the
first match, so a general pattern placed early swallows the specific ones. Two
real misfilings: an application-security vendor filed as vulnerability management
because "vulnerabilit" appears in every appsec description; and a cyber-risk-
quantification vendor filed as exposure management because "financial exposure"
matched a security term doing double duty as an accounting one.

That second class of bug is worse than it looks, because the category chooses the
subject line. A misfiled company gets an email written for somebody else's buyer,
which is worse than sending nothing.

## Verify against known answers

Keep a list of companies you are certain about and assert the gate still returns
the right verdict for all of them after every change. Without that, each fix
silently breaks two things you already got right.
