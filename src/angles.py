"""Stage 4a: what to put in the subject line.

The rule this whole file exists to enforce: **write for the recipient's buyer,
not for the recipient.**

A CRO at a vulnerability-management vendor does not want to read that you admire
their platform. They spend every day listening to their own reps fail to open
conversations with security teams. A subject line that names the problem THEIR
buyer has is a work sample. A subject line about them is a compliment, and
compliments are free, so they carry no information.

Each category holds three angles. Three is deliberate: the subject takes one and
the body gives away the other two. Giving away the other two costs nothing and is
the only part of a cold email that is unarguably useful to the reader even if
they never reply.

A one-line caution learned the expensive way: an earlier version mapped category
to a "buyer" phrase using a lookup table built by guessing. It told a workload-
identity vendor their buyer was "identity and access teams" (they sell to
platform engineers) and told a privacy-tooling vendor their buyer was "CISOs"
(they sell to legal). A generic sentence beats a confidently wrong one.
"""

ANGLES = {
    "Vulnerability mgmt": [
        "CVSS 9.8 doesn't scare your CFO",
        "You patched the CVE, not the exposure",
        "The board doesn't fund a CVSS score",
    ],
    "Exposure / CTEM": [
        "The asset nobody owns is still yours",
        "Your CMDB is a snapshot, not a map",
        "The pentest was true for one week",
    ],
    "Cyber risk / ratings": [
        "Your rating went up, your risk didn't",
        "Compliant vendors still cause breaches",
        "The questionnaire is the real audit",
    ],
    "AppSec / code": [
        "The CVE is in code you didn't write",
        "Your SCA found it, your sprint didn't",
        "The misconfig shipped in your IaC",
    ],
    "EDR / XDR / MDR": [
        "EDR detects, it doesn't contain",
        "The alert fired at 2am, then what",
        "Your SOC closed the ticket, not the gap",
    ],
    "SIEM / SOC": [
        "A full SIEM queue isn't coverage",
        "Someone watched the alert, nobody owned it",
        "Logging an attack isn't stopping it",
    ],
    "Cloud / CNAPP": [
        "Your CSPM found it after it shipped",
        "Lift-and-shift just moves the mess",
        "The role nobody scoped is still assumable",
    ],
    "OT / IoT / ICS": [
        "The plant floor has no patch window",
        "Air-gapped, until the vendor needed access",
        "You inventoried OT. You still can't touch it.",
    ],
    "Identity / IAM": [
        "Most of your IAM isn't a person",
        "The service account nobody rotates",
        "The VPN outlived the office",
    ],
    "Data security": [
        "Classification is a snapshot, copies aren't",
        "DLP saw the file, not the fourth copy",
        "The export was authorised. That's the problem.",
    ],
    "Security (other)": [
        "The control passed, the risk stayed",
        "You bought the tool, not the outcome",
        "Coverage isn't the same as protection",
    ],
}


def pick(category, seed):
    """Choose an angle deterministically from the address.

    Seeding on the recipient's own address rather than a counter means the same
    person always gets the same line, a rebuild is reproducible, and the choice
    survives the list being re-sorted. It also spreads the three angles evenly
    across a batch without any state.
    """
    angles = ANGLES.get(category, ANGLES["Security (other)"])
    primary = angles[seed % len(angles)]
    rest = [a for a in angles if a != primary]
    return primary, rest


def seed_for(email):
    return sum(ord(c) for c in email.strip().lower())
