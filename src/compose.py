"""Build one email per account.

CONFIGURED FOR SIGNOZ. The product block below is the only place the product
appears; swap those four strings to point the engine at something else.

WHY THE COPY LOOKS LIKE THIS

Selling to engineers is not selling with fewer adjectives. It is a different
burden of proof. A VP Engineering can check every claim you make against a
system they know better than you do, so the only durable move is to say
something specific and true and let them verify it.

Rules this file enforces:

  * ONE observation, and it is about their system, not the product.
  * NO adjectives about the product. Nothing is powerful or seamless.
  * The product paragraph states MECHANISM, not benefit. "OpenTelemetry-native,
    so instrumentation is yours" is checkable. "Best-in-class observability" is
    not, and an engineer reads the second one as an admission.
  * NEVER claim open source is cheaper. It is a different cost structure and
    anyone who runs infrastructure knows self-hosting costs engineer-hours.
    Overclaiming here loses a technical reader on line one.
  * 65 to 75 words. Short paragraphs, one idea each.

    python3 -m src.compose data/sample_companies.csv
"""
import csv
import sys

from .angles import pick, seed_for
from .classify import classify

# ---- the only product-specific block in the engine -----------------------
PRODUCT = "SigNoz"
MECHANISM = [
    "SigNoz is OpenTelemetry-native, so the instrumentation stays yours and the "
    "backend stops being a rebuild.",
    "SigNoz reads OTLP directly. No agent in your code, so leaving later costs a "
    "config change, not a re-instrumentation.",
    "SigNoz bills on telemetry volume, not hosts or seats. A different shape of "
    "bill, not a smaller one.",
]
SIGN = "Karan Trivedi"
# --------------------------------------------------------------------------

OPENER = [
    "You will know whether this is true of {company}. It is the pattern on teams "
    "running what you run:",
    "This may not be your situation. It is the common one at your stage:",
    "Worth checking against your own numbers, not mine:",
]

GIVEAWAY = [
    "Two others in the same conversation: {a} / {b}",
    "Two more from that territory: {a} / {b}",
    "Related, and often the actual cause: {a} / {b}",
]

ASK = [
    "Worth twenty minutes?",
    "Open to twenty minutes this week?",
    "Twenty minutes to see whether it applies?",
]


def compose(first_name, email, company, segment):
    """Return (subject, body). Deterministic in the recipient's address."""
    seed = seed_for(email)
    subject, rest = pick(segment, seed)

    blocks = [
        f"Hi {first_name},",
        OPENER[seed % len(OPENER)].format(company=company),
        subject + ".",
        GIVEAWAY[(seed // 3) % len(GIVEAWAY)].format(a=rest[0], b=rest[1]),
        MECHANISM[(seed // 9) % len(MECHANISM)],
        ASK[(seed // 27) % len(ASK)],
        SIGN,
    ]
    return subject, "\n\n".join(blocks)


def main(path):
    rows = list(csv.DictReader(open(path)))
    bodies, built = set(), []

    for r in rows:
        eng = int(r["engineers"]) if r.get("engineers", "").strip().isdigit() else None
        verdict, tier, segment, _reasons = classify(r["company"], r["description"], eng)
        if verdict != "PASS":
            continue
        subject, body = compose(r["first_name"], r["email"], r["company"], segment)
        bodies.add(body)
        built.append((tier, r, subject, body, segment))

    built.sort(key=lambda x: x[0])          # tier 1 first: this is the send order
    for tier, r, subject, body, segment in built:
        print("=" * 74)
        print(f"Tier {tier}  |  {r['first_name']}, {r['role']}, {r['company']}  |  {segment}")
        print(f"Subject: {subject}")
        print(f"Words:   {len(body.split())}")
        print("-" * 74)
        print(body)

    print("=" * 74)
    print(f"{len(built)} emails, {len(bodies)} distinct bodies, tier 1 first.")
    if built and len(bodies) < len(built):
        print("WARNING: duplicate bodies. Add a block or an angle before sending "
              "at volume; identical text is the easiest thing to cluster on.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sample_companies.csv")
