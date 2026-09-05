"""Qualify and PRIORITISE accounts from public evidence.

MARKET-AGNOSTIC. Everything vertical-specific comes from a profile
(`profiles/*.json`); nothing in this file names an industry, a competitor or a
product. Point it at a different market with --profile and the logic is
unchanged, which is the only real test of whether the logic was ever general.

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
import argparse
import csv
import os
import re
import sys

from . import profile as profile_mod

def segment(profile, text):
    """First match wins, so profiles must list most-specific patterns first.

    The segment chooses the subject line, so a misfiled account gets an email
    written for somebody else's problem, which is worse than sending nothing.
    """
    for name, pattern in profile.segments:
        if re.search(pattern, text, re.I):
            return name
    return profile.segments[-1][0]


def classify(profile, company, description, size=None):
    """Return (verdict, tier, segment, reasons).

    verdict: PASS, CHECK or REJECT.  tier: 1 (work first), 2, or 3.
    """
    text = f"{company} {description}"
    reasons = []

    for label, pattern in profile.disqualify.items():
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
    fired = [t for t in profile.triggers if re.search(t["pattern"], text, re.I)]
    names = {t["name"] for t in fired}
    implies_scale = {t["name"] for t in fired if t.get("implies_scale")}

    if re.search(profile.scale_signal, text, re.I):
        reasons.append("runs distributed infrastructure")
    elif implies_scale:
        reasons.append("emits real telemetry (inferred from the trigger, not stated)")
    else:
        return "REJECT", None, "", ["no scale signal: nothing here emits telemetry worth paying for"]

    if not fired:
        # Real infrastructure but no evidence of pain. Not a reject: this is a
        # nurture account, and calling it a reject would delete it from the list
        # permanently. It is simply not this week's work.
        return "CHECK", 3, segment(profile, text), reasons + ["no trigger yet: monitor, do not send"]

    reasons += [t["why"] for t in fired]

    if size is not None:
        unit = profile.size_unit
        if size < profile.min_size:
            return "REJECT", None, "", reasons + [f"{size} {unit}: below the budget floor"]
        if size > profile.max_size:
            return "CHECK", 3, segment(profile, text), reasons + [
                f"{size} {unit}: enterprise motion, not a first-touch account"]

    # Tier by the warmest trigger present, never by company size. A 40-person
    # company with a tier-1 trigger is a better Monday morning than a
    # 900-person company showing nothing but a job post. Sorting a target list
    # by headcount gets this exactly backwards, and most target lists are
    # sorted by headcount.
    tier = min(t["tier"] for t in fired)
    return "PASS", tier, segment(profile, text), reasons


def main():
    ap = argparse.ArgumentParser(description="Qualify and rank accounts from public evidence.")
    ap.add_argument("csv", nargs="?", default="data/sample_observability.csv")
    ap.add_argument("--profile", default="observability",
                    help=f"market profile: {', '.join(profile_mod.available())}")
    a = ap.parse_args()

    try:
        profile = profile_mod.load(a.profile)
    except profile_mod.ProfileError as exc:
        sys.exit(f"[!] {exc}")

    rows = []
    for r in csv.DictReader(open(a.csv)):
        raw = (r.get("size") or r.get("engineers") or "").strip()
        size = int(raw) if raw.isdigit() else None
        verdict, tier, seg, reasons = classify(profile, r["company"], r["description"], size)
        rows.append((verdict, tier or 9, r["company"], seg, reasons))

    order = {"PASS": 0, "CHECK": 1, "REJECT": 2}
    rows.sort(key=lambda x: (order[x[0]], x[1], x[2]))
    width = max(len(r[2]) for r in rows)

    print(f"{profile.market}   [{os.path.basename(profile.path)}]")
    print(f"buyer: {profile.buyer}\n")
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
    main()
