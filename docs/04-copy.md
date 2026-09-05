# 4. Copy

**Code: [`src/angles.py`](../src/angles.py), [`src/compose.py`](../src/compose.py)**

## The one rule

**Write for the recipient's buyer, not for the recipient.**

A CRO at a vulnerability-management vendor does not want to hear that you admire
their platform. They spend every day watching their own reps fail to open
conversations with security teams. A subject line that names the problem *their
buyer* has is a work sample. A subject line about them is a compliment, and
compliments are free, so they carry no information.

This is also the only honest way to prove ability in a cold email. You cannot
claim to be good at writing cold email. You can send one.

## Give the other two away

Each category holds three angles. The subject takes one, the body gives away the
other two. It costs nothing and it is the only part of the email that is useful
to the reader even if they never reply. It also converts the message from a
request into a small gift, which changes what a non-reply feels like on both
sides.

## Length

60 to 65 words. Three short paragraphs: what you do, the terms, the ask.

The version before it was 148 words and included a paragraph on method. Method
answers a question nobody asks first. It was cut and reply rate went up.

## Every body distinct

Identical bodies across a batch are the easiest thing in the world for a receiver
to cluster on. Rotating k blocks of n choices gives n^k variants, which is enough
at any volume worth sending. `compose.py` counts distinct bodies and warns when
the batch has duplicates.

## No merge fields

There is no `{{first_name}} I saw you raised a Series B` anywhere in this. That
sentence is the most-parodied line in the category and it signals a tool rather
than a person. What is personal here is the *argument*: the subject is chosen for
the product the company sells, which is much harder to fake than a merge field.

## A mistake worth copying the fix for

An earlier version mapped each category to a phrase naming that vendor's buyer,
using a lookup table built by guessing rather than research. It told a
workload-identity vendor their buyer was "identity and access teams" when they
sell to platform engineers, and told a privacy-tooling vendor their buyer was
"CISOs" when they sell to legal.

Both errors are invisible to the sender and obvious to the reader, which is the
worst combination available. The fix was to delete the line. **A generic sentence
beats a confidently wrong one.**
