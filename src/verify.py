"""Stages 3 and 5: does this mailbox exist, and will your mail be trusted?

TWO SEPARATE QUESTIONS, AND ONE OF THEM IS NOT ANSWERABLE

  1. "Has this person left the company?"  Unanswerable from here. In one audit
     of 936 stored contacts, 41% had moved on. A contact is a claim with a
     timestamp, never a fact.

  2. "Will this address accept mail?"  Answerable, partly. That is the question
     worth asking, because it is the one with a mechanical answer.

WHAT AN SMTP PROBE ACTUALLY SETTLES

MX-checking proves only that the DOMAIN receives mail, which almost every live
company does, so it has near-zero discriminating power. The individual mailbox
needs port 25 and an RCPT probe, and even then it resolves maybe half:

    Google Workspace   most tenants accept every RCPT -> proves nothing
    Microsoft 365      unknown users usually 550       -> usually decisive
    self-hosted        usually decisive
    Proofpoint         often decisive

So roughly 45% of a typical B2B list is unverifiable this way at any price. For
those, the RAMP is the verifier: send them early in small tranches and let the
4% circuit breaker in guards.py stop the batch after about one bounce in
twenty-five. That costs a few bounces instead of a subscription, which at low
volume is the proportionate answer.

This module ships the MX check only. Deliberately: a working RCPT prober is a
list-validation tool, and publishing one helps spammers more than it helps
anyone reading this.

    python3 -m src.verify --mx example.com
"""
import argparse
import socket

try:
    import dns.resolver           # optional; falls back to a socket probe
    HAVE_DNS = True
except ImportError:
    HAVE_DNS = False


def has_mx(domain, timeout=5.0):
    """Does this domain accept mail? Proves the company exists, not the person."""
    if HAVE_DNS:
        try:
            answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
            return True, sorted(str(r.exchange).rstrip(".") for r in answers)
        except Exception as exc:
            return False, [f"{type(exc).__name__}"]
    # No dnspython: a resolvable A record is weak evidence, and says so.
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(domain)
        return True, ["resolves (no MX lookup: pip install dnspython)"]
    except Exception as exc:
        return False, [f"{type(exc).__name__}"]


AUTH_NOTES = """
DELIVERABILITY: get this right BEFORE the first send, not after

  SPF     one record only. Two is an RFC 7208 PermError and is worse than one
          wrong record. Ending in -all while your real sender is not listed is
          a hard fail at every receiver, every time.
  DKIM    a published DNS record is NOT the same as signing being switched on.
          A record with signing disabled is the failure that looks like success.
  DMARC   start at p=none during warmup, move to quarantine once passes are
          clean. Point rua at a mailbox someone actually reads.

Verify by sending one message to a Gmail address and opening "Show original":
SPF, DKIM and DMARC must all say PASS. Then cross-check on mail-tester.com.

Cost of skipping this: a domain whose SPF hard-failed sent two dozen cold emails
that were probably filtered on arrival. Zero bounces, zero replies. Bounces tell
you an address is dead; silence tells you nothing, which is why authentication
failures are so expensive. You cannot tell them apart from bad copy.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mx", metavar="DOMAIN", help="check a domain accepts mail")
    ap.add_argument("--notes", action="store_true", help="deliverability checklist")
    a = ap.parse_args()

    if a.mx:
        ok, detail = has_mx(a.mx)
        print(f"{a.mx}: {'accepts mail' if ok else 'NO MX'}")
        for d in detail:
            print(f"  {d}")
        if ok:
            print("\n  Note: this proves the DOMAIN receives mail. It says nothing\n"
                  "  about whether this particular person still works there.")
    elif a.notes:
        print(AUTH_NOTES)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
