"""Stage 4b: build one email per company.

Two properties are non-negotiable and both are anti-fingerprint measures:

  * every body is DISTINCT. Identical bodies across a batch are the single
    easiest thing for a receiver to cluster on. Rotating blocks gives n^k
    variants from k blocks of n, which is enough at any volume worth sending.
  * every body is SHORT. Long cold emails are not read. The version that
    actually got replies is 60 to 65 words: what you do, the terms, the ask.

There is no personalisation token anywhere in here, on purpose. "I saw you raised
a Series B" is the most-parodied sentence in the category and it signals a tool,
not a person. What is personal in these emails is the ARGUMENT: the subject line
is picked for the product the company sells, which is a harder thing to fake than
a merge field.

    python3 -m src.compose data/sample_companies.csv
"""
import csv
import sys

from .angles import pick, seed_for
from .classify import classify

OPENER = [
    "Your reps are writing to security buyers who already delete most of what they get.",
    "The hard part of your funnel is the first email, not the demo.",
    "Getting a security buyer to reply is a different job from selling them.",
]

GIVEAWAY = [
    "That subject line is one I'd send for you. Two more for the same buyer: {a} / {b}",
    "Above is a live sample. Two others aimed at the same buyer: {a} / {b}",
    "That line is the work, not a claim about it. Two more: {a} / {b}",
]

ASK = [
    "Worth twenty minutes?",
    "Open to twenty minutes this week?",
    "Twenty minutes to see if it fits?",
]

SIGN = "Karan Trivedi"


def compose(first_name, email, category):
    """Return (subject, body). Deterministic in the address."""
    seed = seed_for(email)
    subject, rest = pick(category, seed)

    blocks = [
        f"Hi {first_name},",
        OPENER[(seed // 1) % len(OPENER)],
        GIVEAWAY[(seed // 3) % len(GIVEAWAY)].format(a=rest[0], b=rest[1]),
        ASK[(seed // 9) % len(ASK)],
        SIGN,
    ]
    return subject, "\n\n".join(blocks)


def main(path):
    rows = list(csv.DictReader(open(path)))
    bodies, sent = set(), 0

    for r in rows:
        verdict, _reason, category = classify(r["company"], r["description"])
        if verdict != "PASS":
            continue
        subject, body = compose(r["first_name"], r["email"], category)
        bodies.add(body)
        sent += 1
        print("=" * 72)
        print(f"To:      {r['first_name']} at {r['company']}  [{category}]")
        print(f"Subject: {subject}")
        print(f"Words:   {len(body.split())}")
        print("-" * 72)
        print(body)

    print("=" * 72)
    print(f"{sent} emails, {len(bodies)} distinct bodies.")
    if sent and len(bodies) < sent:
        print("WARNING: duplicate bodies in the batch. Add a block or an angle "
              "before sending at volume; identical text is what gets clustered.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sample_companies.csv")
