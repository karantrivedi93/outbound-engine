"""Stage 2: is this company a product vendor, or a reseller wearing the words?

The first version of this gate scored keywords and let IT-services firms,
resellers and trade media through, because those all describe security in the
same vocabulary a security vendor uses. Counting words cannot separate them.

What does separate them is ORDER. The gate runs as a fixed sequence of tests and
stops at the first that fires:

    1. hard reject   reseller / distributor / training / media / recruiter
    2. product?      must show it sells software it built
    3. security?     must be about security at all
    4. tie-break     product AND services language -> CHECK, do not guess

Step 4 is the one that matters. A vendor with a managed-service arm looks exactly
like a reseller to a keyword counter. Rapid7 sells products and MDR; a pure
reseller has the services language and nothing behind it. When both signals are
present the row is flagged for a human instead of being decided by whichever list
happened to be longer.

    python3 -m src.classify data/sample_companies.csv
"""
import csv
import re
import sys

# Order matters in this file. These are tried first and end the decision.
HARD_REJECT = {
    "reseller":    r"\b(reseller|resell|distributor|value[- ]added reseller|VAR|channel partner)\b",
    "integrator":  r"\b(system integrator|systems integration|IT services|staff augmentation)\b",
    "training":    r"\b(training institute|certification course|bootcamp|academy)\b",
    "media":       r"\b(magazine|news portal|editorial|conference organiser|media house)\b",
    "recruiting":  r"\b(recruitment agency|staffing firm|talent solutions)\b",
}

# Evidence the company ships software of its own.
PRODUCT = r"\b(platform|product|software|SaaS|engine|agent|sensor|console|API|dashboard)\b"

# Evidence the subject is security.
#
# The acronyms are load-bearing, not decoration. The first version of this
# pattern held only the spelled-out words, and a company describing itself as an
# "XDR platform" or doing "managed detection and response" matched none of them.
# It was then rejected for not being a security company, which is the worst kind
# of failure this gate can produce: a silent, confident false negative on exactly
# the vendors most worth reaching. Anything used as a category below must be
# recognisable here too.
SECURITY = (r"\b(security|cyber|threat|vulnerabilit|exposure|risk|identity|complian"
            r"|attack surface|malware|phishing|breach|intrusion|endpoint"
            r"|detection and response"
            r"|EDR|XDR|MDR|NDR|SIEM|SOAR|SOC|IAM|PAM|DLP|CNAPP|CSPM|CTEM|EASM|GRC|TPRM)\b")

# Services language. On its own this is disqualifying; alongside a product
# signal it means "vendor with a services arm", which is a CHECK, not a reject.
SERVICES = r"\b(consulting|advisory|managed services|implementation partner|audit services|professional services)\b"

# ORDER MATTERS HERE TOO, and it is the opposite of obvious.
#
# categorise() returns the FIRST pattern that matches, so the list must run from
# most specific to most general. Two real mistakes from the first ordering:
#
#   "Application security platform, SCA, supply chain" -> Vulnerability mgmt,
#   because "vulnerabilit" appears in every appsec description ever written.
#
#   "Cyber risk quantification, turns findings into financial exposure"
#   -> Exposure / CTEM, because the word "exposure" was doing double duty as a
#   security term and an accounting term.
#
# Both were wrong in the direction that matters: the subject line is chosen from
# the category, so a misfiled company gets an email written for somebody else's
# buyer. That is worse than sending nothing.
CATEGORIES = [
    ("Cyber risk / ratings", r"risk quantif|cyber risk|security rating|\bFAIR\b|\bCRQ\b"),
    ("AppSec / code",        r"appsec|application security|\bSAST\b|\bDAST\b|\bSCA\b"
                             r"|supply chain|dependenc|open source"),
    ("OT / IoT / ICS",       r"\bOT\b|\bICS\b|\bIoT\b|plant floor|industrial control"),
    ("Identity / IAM",       r"\bIAM\b|\bPAM\b|identity|privileged access|non-human identit"),
    ("Cloud / CNAPP",        r"\bCNAPP\b|\bCSPM\b|cloud security|kubernetes"),
    ("EDR / XDR / MDR",      r"\bEDR\b|\bXDR\b|\bMDR\b|endpoint|detection and response"),
    ("SIEM / SOC",           r"\bSIEM\b|\bSOAR\b|\bSOC\b|detection engineer"),
    ("Data security",        r"\bDLP\b|data security|data protection|classification"),
    ("Exposure / CTEM",      r"attack surface|exposure management|\bCTEM\b|\bEASM\b"),
    ("Vulnerability mgmt",   r"vulnerabilit|patch|remediation"),
]


def categorise(text):
    for name, pattern in CATEGORIES:
        if re.search(pattern, text, re.I):
            return name
    return "Security (other)"


def classify(name, description):
    """Return (verdict, reason, category).

    verdict is PASS, REJECT or CHECK. The reason is always specific enough that
    a human can disagree with it, which is the only way a gate like this gets
    corrected instead of trusted.
    """
    text = f"{name} {description}"

    for label, pattern in HARD_REJECT.items():
        hit = re.search(pattern, text, re.I)
        if hit:
            return "REJECT", f"hard reject: {label} ({hit.group(0)!r})", ""

    has_product  = bool(re.search(PRODUCT, text, re.I))
    has_security = bool(re.search(SECURITY, text, re.I))
    has_services = bool(re.search(SERVICES, text, re.I))

    if not has_security:
        return "REJECT", "no security signal", ""
    if not has_product:
        return "REJECT", "security, but no product signal (services only)", ""
    if has_services:
        # Both signals. Could be a real vendor with a services arm, could be a
        # consultancy that also licenses a tool. Not a guess worth making.
        return "CHECK", "product AND services language; needs a human", categorise(text)

    return "PASS", "product signal, security signal, no services language", categorise(text)


def main(path):
    counts = {"PASS": 0, "REJECT": 0, "CHECK": 0}
    rows = list(csv.DictReader(open(path)))
    width = max(len(r["company"]) for r in rows)

    for r in rows:
        verdict, reason, category = classify(r["company"], r["description"])
        counts[verdict] += 1
        print(f"{verdict:<7} {r['company']:<{width}}  {category or '-':<20} {reason}")

    total = sum(counts.values())
    print(f"\n{total} companies -> {counts['PASS']} pass, "
          f"{counts['CHECK']} need review, {counts['REJECT']} rejected")
    print("CHECK rows are not failures. They are the rows where guessing would "
          "have been wrong about half the time.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sample_companies.csv")
