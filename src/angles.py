"""Subject lines, by the situation the prospect is actually in.

Configured for an OpenTelemetry-native observability platform sold to
engineering teams: SigNoz's market. Swap this file to retarget the engine; every
other module reads categories from it and none of them hard-code a vertical.

THE RULE THIS FILE ENFORCES

Write about the reader's *system*, not about your product. An engineering leader
does not want to hear that your platform is unified and powerful. They want to
know you understand why their observability bill grew 40% while their traffic
grew 8%, and what specifically caused it.

That distinction matters more selling to engineers than to any other buyer.
Engineers are the audience most reliably repelled by marketing register and the
most rewarding once you're past it, because a correct technical observation is
checkable and a claim is not.

WHAT NOT TO WRITE

- No adjectives about the product. "Powerful", "seamless", "next-generation"
  and "revolutionary" all read as noise to this buyer.
- No "quick question". No "just circling back". No fake thread.
- Never say open source is cheaper. It is a different cost structure, and
  someone who runs infrastructure knows self-hosting has a real bill in
  engineer-hours. Overclaiming here loses a technical reader on line one.

Three angles per segment: the subject takes one, the body gives away the other
two. Giving them away costs nothing and makes the email useful even to someone
who never replies.
"""

ANGLES = {
    "Cost / bill growth": [
        "Your observability bill grew faster than your traffic",
        "Custom metrics are the line item nobody forecast",
        "Per-host pricing and autoscaling are a bad match",
    ],
    "Vendor lock-in": [
        "The agent in your code is the switching cost",
        "Instrumentation you can't take with you",
        "Re-instrumenting is the reason you haven't moved",
    ],
    "OpenTelemetry migration": [
        "You adopted OTel, then paid to have it re-mapped",
        "OTel-compatible and OTel-native are different bills",
        "Your traces are already standard. Your backend isn't.",
    ],
    "Tool sprawl": [
        "Three tabs to answer one question",
        "Metrics here, traces there, the incident somewhere else",
        "Correlating an incident shouldn't be a copy-paste job",
    ],
    "Log volume / retention": [
        "You sample logs to afford them",
        "Retention is a budget decision, not an engineering one",
        "The log you needed was the one you dropped",
    ],
    "Cardinality": [
        "High cardinality is where the answer is, and the bill",
        "You dropped the label that would have found it",
        "Cardinality limits are a pricing decision in a config file",
    ],
    "Self-host / residency": [
        "Some telemetry can't leave the VPC",
        "Compliance says self-host, the vendor says cloud",
        "Your data residency answer is currently a slide",
    ],
    "Kubernetes / ephemeral": [
        "Billed per host for pods that live 40 seconds",
        "Autoscaling is a pricing event, not just a capacity one",
        "Node count stopped predicting anything",
    ],
    "Scaling past CloudWatch": [
        "You outgrew CloudWatch and can't justify Datadog",
        "Grafana plus Loki plus Tempo is three upgrades to run",
        "The stack was free until someone had to maintain it",
    ],
    "AI / LLM workloads": [
        "Your LLM calls are the spans you aren't tracing",
        "Token spend is a latency problem wearing a finance hat",
        "You can see the request, not what the model cost",
    ],
}


def pick(category, seed):
    """Choose an angle deterministically from the recipient's address.

    Seeding on the address rather than a counter means the same person always
    gets the same line, a rebuild is reproducible, and the choice survives the
    list being re-sorted. It also spreads angles evenly with no state.
    """
    angles = ANGLES.get(category, ANGLES["Cost / bill growth"])
    primary = angles[seed % len(angles)]
    rest = [a for a in angles if a != primary]
    return primary, rest


def seed_for(email):
    return sum(ord(c) for c in email.strip().lower())
