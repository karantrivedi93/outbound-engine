"""Stage 6: the guards.

WHY THIS FILE EXISTS
--------------------
On one day a campaign sent 470 emails against a plan of 35. 297 of them went out
between midnight and 05:00, to a list that was almost entirely in US time zones.

Nothing was malicious and nobody was careless. `--daily-cap 35` was a PER-RUN
cap with no memory, so five invocations of the same command meant five caps. The
operator's intent was correct every single time; the program simply had no way to
know what it had already done.

That is the whole lesson. A limit that depends on the operator remembering is not
a limit, it is a preference. Everything below is enforced by the program and
cannot be satisfied by intending to satisfy it.

    python3 -m src.guards --demo
"""
import argparse
import re
import time

# --- the ramp -------------------------------------------------------------
# (day number counted from this sender's FIRST EVER send, ceiling from then on).
# A new domain that sends 200 emails on day one has told every receiver exactly
# what it is. Warming is not superstition; it is the only signal a cold domain
# can send about itself.
RAMP = [(1, 10), (4, 15), (7, 20), (10, 25)]
SEND_HOURS = (8, 23)
BOUNCE_STOP = 0.04     # hard stop if the failure rate passes 4%

# --- the blocklist --------------------------------------------------------
# Four layers, checked in order, failing CLOSED: anything unparseable is blocked
# rather than allowed. Layer 4 runs immediately before each individual API call,
# not just once at startup, because a batch can be mutated between validation
# and send.
BLOCKED_EXACT = {"abuse@", "postmaster@", "noreply@", "no-reply@"}
BLOCKED_DOMAINS = {"example.com", "example.org", "example.net", "test.com"}
BLOCKED_TLDS = {".gov", ".mil", ".edu"}
ROLE_PREFIXES = {"info", "sales", "support", "admin", "contact", "hello", "help"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


def is_blocked(email, suppressed=frozenset()):
    """Return a reason string if this address must not be emailed, else None.

    Fails closed: an address that cannot be parsed is blocked. The default in a
    sender is always 'do not send'.
    """
    if not email or not isinstance(email, str):
        return "empty or non-string address"
    addr = email.strip().lower()
    if not EMAIL_RE.match(addr):
        return f"unparseable address: {email!r}"

    local, _, domain = addr.partition("@")

    if any(addr.startswith(p) for p in BLOCKED_EXACT):
        return f"reserved mailbox: {local}@"
    if domain in BLOCKED_DOMAINS:
        return f"blocked domain: {domain}"
    if any(domain.endswith(t) for t in BLOCKED_TLDS):
        return f"blocked TLD on {domain}"
    if local in ROLE_PREFIXES:
        return f"role address, not a person: {local}@"
    # Suppression is by DOMAIN, not address. Someone who asked to be left alone
    # did not mean "write to my colleague instead".
    if domain in suppressed:
        return f"suppressed domain: {domain}"
    return None


def ramp_cap(day):
    """Ceiling for this day number. --daily-cap may only LOWER this."""
    cap = RAMP[0][1]
    for start, value in RAMP:
        if day >= start:
            cap = value
    return cap


def hours_ok(now=None):
    """Weekdays inside business hours, or a reason why not.

    Known limitation, stated because it matters: this reads the SENDER's clock.
    For a list in another hemisphere it is the wrong question, and a guard that
    has to be overridden routinely is the shape of the next incident. The right
    version is recipient-aware.
    """
    now = now or time.localtime()
    if now.tm_wday >= 5:
        return False, f"{time.strftime('%A', now)}: weekdays only"
    lo, hi = SEND_HOURS
    if not (lo <= now.tm_hour < hi):
        return False, f"{now.tm_hour:02d}:00 is outside {lo:02d}:00-{hi:02d}:00"
    return True, ""


def allowance(day, already_sent_today, requested_cap):
    """How many may be sent right now.

    The critical line is `already_sent_today`. It is read back from the log the
    sender was already writing on every send and that nothing ever read. That one
    missing read is the entire 470-email incident.
    """
    ceiling = min(ramp_cap(day), requested_cap)
    return max(0, ceiling - already_sent_today)


def should_stop(attempted, failed):
    """Circuit breaker. A batch of dead addresses halts itself."""
    if attempted < 25:
        return False, ""
    rate = failed / attempted
    if rate > BOUNCE_STOP:
        return True, f"failure rate {rate:.1%} over {BOUNCE_STOP:.0%}; stopping"
    return False, ""


def demo():
    print("BLOCKLIST (fails closed)")
    for addr in ["alex@vendor.io", "info@vendor.io", "abuse@vendor.io",
                 "someone@example.com", "clerk@agency.gov", "not-an-email",
                 "", "jo@quiet-co.io"]:
        why = is_blocked(addr, suppressed={"quiet-co.io"})
        print(f"  {addr!r:<26} {'BLOCK  ' + why if why else 'allow'}")

    print("\nRAMP (--daily-cap can only lower these)")
    for day in (1, 3, 4, 6, 7, 10, 40):
        print(f"  day {day:<3} ceiling {ramp_cap(day)}")

    print("\nALLOWANCE — the fix for the 470-email day")
    print(f"  day 4, cap 15, nothing sent yet     -> {allowance(4, 0, 15)}")
    print(f"  day 4, cap 15, 12 already sent      -> {allowance(4, 12, 15)}")
    print(f"  day 4, cap 15, 15 already sent      -> {allowance(4, 15, 15)}  <- second run sends nothing")
    print(f"  day 4, --daily-cap 5 (lower)        -> {allowance(4, 0, 5)}")
    print(f"  day 4, --daily-cap 99 (cannot raise)-> {allowance(4, 0, 99)}")

    ok, why = hours_ok()
    print(f"\nHOURS  now: {'ok' if ok else 'REFUSED — ' + why}")

    print("\nCIRCUIT BREAKER")
    for attempted, failed in [(10, 3), (100, 2), (100, 9)]:
        stop, why = should_stop(attempted, failed)
        print(f"  {failed}/{attempted:<5} {'STOP — ' + why if stop else 'continue'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    if ap.parse_args().demo:
        demo()
    else:
        ap.print_help()
