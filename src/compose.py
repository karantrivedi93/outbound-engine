"""Build one email per account.

MARKET-AGNOSTIC. The product sentences and the subject lines come from the
loaded profile (`profiles/*.json`); the product NAME comes from --product.
Nothing in this file names a market, a company or a product.

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
import argparse
import csv
import sys

from . import profile as profile_mod

from .angles import pick, seed_for
from .classify import classify

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


def compose(profile, first_name, email, company, segment, product="Acme", sign="Karan Trivedi"):
    """Return (subject, body). Deterministic in the recipient's address."""
    seed = seed_for(email)
    subject, rest = pick(profile, segment, seed)
    mechanism = profile.mechanism[(seed // 9) % len(profile.mechanism)]

    blocks = [
        f"Hi {first_name},",
        OPENER[seed % len(OPENER)].format(company=company),
        subject + ".",
        GIVEAWAY[(seed // 3) % len(GIVEAWAY)].format(a=rest[0], b=rest[1]),
        mechanism.format(product=product),
        ASK[(seed // 27) % len(ASK)],
        sign,
    ]
    return subject, "\n\n".join(blocks)


def main():
    ap = argparse.ArgumentParser(description="Build one email per qualified account.")
    ap.add_argument("csv", nargs="?", default="data/sample_observability.csv")
    ap.add_argument("--profile", default="observability",
                    help=f"market profile: {', '.join(profile_mod.available())}")
    ap.add_argument("--product", default="Acme", help="your product's name")
    ap.add_argument("--sign", default="Karan Trivedi")
    a = ap.parse_args()

    try:
        profile = profile_mod.load(a.profile)
    except profile_mod.ProfileError as exc:
        sys.exit(f"[!] {exc}")

    bodies, built = set(), []
    for r in csv.DictReader(open(a.csv)):
        raw = (r.get("size") or r.get("engineers") or "").strip()
        size = int(raw) if raw.isdigit() else None
        verdict, tier, segment, _why = classify(profile, r["company"], r["description"], size)
        if verdict != "PASS":
            continue
        subject, body = compose(profile, r["first_name"], r["email"], r["company"],
                                segment, a.product, a.sign)
        bodies.add(body)
        built.append((tier, r, subject, body, segment))

    built.sort(key=lambda x: x[0])          # tier 1 first: this IS the send order
    for tier, r, subject, body, segment in built:
        print("=" * 74)
        print(f"Tier {tier}  |  {r['first_name']}, {r.get('role', '?')}, {r['company']}  |  {segment}")
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
    main()
