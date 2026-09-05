# 4. Copy

**Code: [`src/angles.py`](../src/angles.py), [`src/compose.py`](../src/compose.py)**

The rules are market-agnostic; the subject lines and product sentences come from
the loaded profile. Examples below use the observability profile.

## Selling to engineers is a different burden of proof

Not "the same email with fewer adjectives". A VP Engineering can check every
claim you make against a system they know far better than you do. That single
fact determines everything below.

So: say one specific, checkable, true thing about *their* system, and let them
verify it. That is the only move that survives contact with this buyer.

## The rules, each with a test behind it

**One observation, about their system, not your product.**
*"Billed per host for pods that live 40 seconds"* is checkable against their own
invoice. *"Modern observability for cloud-native teams"* is not checkable against
anything.

**No adjectives about the product.** Nothing is powerful, seamless,
best-in-class, next-generation or game-changing.
`test_no_marketing_adjectives_survive` fails the build on eight of them, across
every segment, because this is the failure that creeps back in.

**Mechanism, not benefit.** *"Reads OTLP directly, no agent in your code, so
leaving later costs a config change rather than a re-instrumentation"* is a fact
with consequences the reader can work out themselves. *"Unified observability"*
is a claim. A technical reader hears the second as an admission that there was
nothing checkable to say.

**Never claim open source is cheaper.** It is a *different cost structure*.
Anyone who runs infrastructure knows self-hosting has a real bill in
engineer-hours, and someone evaluating a self-hostable tool has already thought
about it more carefully than you have. Overclaim here and you lose them on line
one, permanently, and they will be right to go.

**Give away the two angles the subject did not use.** It costs nothing and makes
the email useful to someone who never replies. It also changes the message from a
request into a small gift, which changes what a non-reply feels like on both
sides.

**65 to 75 words.** Long cold emails are not read. An earlier version ran to 148
with a paragraph on method; method answers a question nobody asks first. Cutting
it raised reply rate.

## No merge fields

There is no `{{first_name}}, I saw you raised a Series B` anywhere in this. That
sentence is the most-parodied line in the category and signals a tool rather than
a person.

What is personal here is the **argument**: the segment is chosen from public
evidence about their stack, and the subject line is chosen from the segment.
That is much harder to fake than a merge field, and much harder to automate
badly.

## The mistake worth copying the fix for

An earlier system mapped each category to a phrase naming that company's buyer,
from a lookup table built by guessing rather than research. It told a
workload-identity vendor their buyer was "identity and access teams" when they
sell to platform engineers.

Invisible to the sender, obvious to the reader — the worst combination available.
The fix was to delete the line. **A generic sentence beats a confidently wrong
one.**

## What this does not cover

For an open-source developer tool, cold email is one channel and not the largest.
Most of the pipeline arrives through the repository, the docs, the community
Slack and people who already ran `docker compose up` before anyone spoke to them.

Outbound's honest job in that setting is narrower and still worth doing: reach
the teams who have the problem, are already paying someone else for it, and have
not yet heard that a self-hostable OpenTelemetry-native option exists. Everything
in this repository is built for that job and not for volume.
