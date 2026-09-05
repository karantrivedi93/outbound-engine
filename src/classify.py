"""Qualify and PRIORITISE accounts from public evidence.

A list is not a target list until it is ordered. Filtering answers "could I
email this company"; ranking answers "who do I email on Monday morning", and
only the second one is the job. A founding SDR with 400 plausible accounts and
no order will work them alphabetically, which means working them by accident.

WHAT THIS GATE ASKS, IN ORDER

    1. disqualify   competitor, agency, or no engineering org at all
    2. scale?       do they run something that produces real telemetry
    3. trigger?     is there evidence they are unhappy or already moving
    4. size band?   too small has no budget, too large is a different motion
    5. rank         tier by how warm the trigger is, not by company size

THE THREE TRIGGERS, WARMEST FIRST

    OpenTelemetry mentioned    They have already done the expensive half of the
                               migration. The instrumentation is portable and
                               the backend is now a choice rather than a
                               rebuild. Warmest signal available.

    Incumbent named            Datadog, New Relic, Dynatrace, Splunk. There is
                               a bill, an owner and a renewal date. You are
                               displacing something, which is harder than
                               greenfield but the budget already exists.

    Hiring SRE / platform      Somebody signed off on headcount for reliability.
                               Budget and pain both exist; the specific tool
                               complaint is not yet visible.

Every verdict carries its evidence, because a ranking nobody can argue with is a
ranking nobody will correct.

    python3 -m src.classify data/sample_companies.csv
"""
import csv
import re
import sys

# Checked first; these end the decision.
DISQUALIFY = {
    "competitor":  r"\b(observability platform|APM vendor|monitoring vendor|we provide monitoring)\b",
    "agency":      r"\b(digital agency|consultancy|consulting firm|staff augmentation|outsourcing partner)\b",
    "reseller":    r"\b(reseller|distributor|channel partner|value[- ]added reseller)\b",
    "no eng org":  r"\b(law firm|accounting firm|recruitment agency|real estate brokerage)\b",
}

# Do they run something that emits meaningful telemetry?
#
# Note the optional plurals. The first version ended each alternative at a word
# boundary, so \bmicroservice\b did not match "microservices" and \bcontainer\b
# did not match "containers" — which is how every engineering blog on earth
# actually writes them. Three of twelve sample companies were rejected for
# owning infrastructure they had described in the plural.
SCALE = (r"\b(microservices?|kubernetes|k8s|distributed systems?|containers?|service mesh"
         r"|event[- ]driven|high[- ]throughput|multi[- ]region|serverless|data pipelines?)\b")

# Triggers, warmest first. Order here IS the priority order.
TRIGGERS = [
    ("otel",      r"\b(opentelemetry|otel|otlp)\b",
                  "already on OpenTelemetry: instrumentation is portable, backend is a choice"),
    ("incumbent", r"\b(datadog|new relic|dynatrace|splunk|appdynamics|honeycomb|grafana cloud)\b",
                  "names an incumbent: there is a bill, an owner and a renewal date"),
    ("hiring",    r"\b(hiring|we're looking for|join our team).{0,80}\b(SRE|site reliability|platform engineer|devops|observability)\b",
                  "hiring reliability headcount: budget and pain both exist"),
]

# Which pain to lead with. Most specific first: categorise() returns the first
# match, so a general pattern placed early swallows the specific ones.
SEGMENTS = [
    ("AI / LLM workloads",      r"\b(LLM|inference|GenAI|model serving|vector database)\b"),
    ("Self-host / residency",   r"\b(data residency|self[- ]host|on[- ]prem|air[- ]gapped|sovereignty|HIPAA|PCI)\b"),
    ("OpenTelemetry migration", r"\b(opentelemetry|otel|otlp)\b"),
    ("Kubernetes / ephemeral",  r"\b(kubernetes|k8s|autoscal|ephemeral|spot instance)\b"),
    ("Log volume / retention",  r"\b(log volume|log retention|log ingestion|petabyte|terabytes of logs)\b"),
    ("Cardinality",             r"\b(cardinality|label explosion|high[- ]dimension)\b"),
    ("Tool sprawl",             r"\b(multiple tools|tool sprawl|stitching|three different|context switch)\b"),
    ("Scaling past CloudWatch", r"\b(cloudwatch|prometheus|loki|tempo|self[- ]managed grafana)\b"),
    ("Vendor lock-in",          r"\b(lock[- ]in|proprietary agent|vendor agent|migration cost)\b"),
    ("Cost / bill growth",      r"\b(cost|bill|spend|budget|expensive|pricing)\b"),
]

# Below this there is no budget; above it, it is an enterprise motion with a
# procurement cycle, which is not what a founding SDR should spend week one on.
MIN_ENG, MAX_ENG = 15, 2000


def segment(text):
    for name, pattern in SEGMENTS:
        if re.search(pattern, text, re.I):
            return name
    return "Cost / bill growth"


def classify(company, description, engineers=None):
    """Return (verdict, tier, segment, reasons).

    verdict: PASS, CHECK or REJECT.  tier: 1 (work first), 2, or 3.
    """
    text = f"{company} {description}"
    reasons = []

    for label, pattern in DISQUALIFY.items():
        hit = re.search(pattern, text, re.I)
        if hit:
            return "REJECT", None, "", [f"disqualified: {label} ({hit.group(0)!r})"]

    # Triggers are found BEFORE the scale test, because two of them settle it.
    # An earlier version demanded an architecture keyword first and rejected the
    # warmest account in the sample: a company already running OpenTelemetry
    # collectors and migrating off New Relic, thrown out for never using the
    # word "microservices". Anyone emitting OTLP or paying an APM vendor has
    # already proved they produce telemetry worth paying for. Requiring them to
    # also say the magic word tests their copywriting, not their architecture.
    fired = [(name, why) for name, pattern, why in TRIGGERS if re.search(pattern, text, re.I)]
    names = {n for n, _ in fired}

    if re.search(SCALE, text, re.I):
        reasons.append("runs distributed infrastructure")
    elif names & {"otel", "incumbent"}:
        reasons.append("emits real telemetry (inferred from the trigger, not stated)")
    else:
        return "REJECT", None, "", ["no scale signal: nothing here emits telemetry worth paying for"]

    if not fired:
        # Real infrastructure but no evidence of pain. Not a reject: this is a
        # nurture account, and calling it a reject would delete it from the list
        # permanently. It is simply not this week's work.
        return "CHECK", 3, segment(text), reasons + ["no trigger yet: monitor, do not send"]

    reasons += [why for _name, why in fired]

    if engineers is not None:
        if engineers < MIN_ENG:
            return "REJECT", None, "", reasons + [f"{engineers} engineers: below the budget floor"]
        if engineers > MAX_ENG:
            return "CHECK", 3, segment(text), reasons + [
                f"{engineers} engineers: enterprise motion, not a founding-SDR first touch"]

    # Tier by the warmest trigger present, never by company size. A 40-engineer
    # company already running OTel is a better Monday morning than a 900-engineer
    # company with nothing but a job post.
    tier = 1 if ("otel" in names or "incumbent" in names) else 2
    return "PASS", tier, segment(text), reasons


def main(path):
    rows = []
    for r in csv.DictReader(open(path)):
        eng = int(r["engineers"]) if r.get("engineers", "").strip().isdigit() else None
        verdict, tier, seg, reasons = classify(r["company"], r["description"], eng)
        rows.append((verdict, tier or 9, r["company"], seg, reasons))

    order = {"PASS": 0, "CHECK": 1, "REJECT": 2}
    rows.sort(key=lambda x: (order[x[0]], x[1], x[2]))
    width = max(len(r[2]) for r in rows)

    print(f"{'VERDICT':<8}{'TIER':<6}{'COMPANY':<{width + 2}}{'LEAD WITH':<26}WHY")
    print("-" * (44 + width + 26))
    for verdict, tier, company, seg, reasons in rows:
        t = "-" if tier == 9 else str(tier)
        print(f"{verdict:<8}{t:<6}{company:<{width + 2}}{seg or '-':<26}{reasons[-1]}")
        for extra in reasons[:-1]:
            print(f"{'':<14}{'':<{width + 2}}{'':<26}{extra}")

    p1 = sum(1 for r in rows if r[0] == "PASS" and r[1] == 1)
    p2 = sum(1 for r in rows if r[0] == "PASS" and r[1] == 2)
    print(f"\nTier 1: {p1} work these first.  Tier 2: {p2}.  "
          f"Nurture: {sum(1 for r in rows if r[0] == 'CHECK')}.  "
          f"Rejected: {sum(1 for r in rows if r[0] == 'REJECT')}.")
    print("Tier is set by how warm the trigger is, never by company size.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sample_companies.csv")
