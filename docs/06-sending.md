# 6. Sending

**Code: [`src/guards.py`](../src/guards.py) · run `python3 -m src.guards --demo`**

## The incident this file exists because of

One day, a campaign sent **470 emails against a plan of 35**. 297 of them went
out between midnight and 05:00, to a list that was almost entirely US-based.

The cause: `--daily-cap 35` was a **per-run** cap with no memory. Five
invocations meant five caps. The sender had been faithfully writing a timestamp
on every send since day one, and nothing had ever read it back.

Nobody was careless. The operator's intent was correct on every single run. The
program simply had no way to know what it had already done.

**A limit that depends on the operator remembering is not a limit. It is a
preference.**

## The guards

**A true per-day cap.** `sent_today()` reads back the log. The run is capped at
today's *remainder*, so a second invocation of the same command sends the rest or
nothing.

**An enforced ramp.** A ceiling by day number counted from that sender's first
ever send. `--daily-cap` can only *lower* it; raising it needs an explicit
override flag and a typed confirmation.

```
day 1-3 -> 10    day 4-6 -> 15    day 7-9 -> 20    day 10+ -> 25
```

**Hours and weekdays.** Refused outside business hours without an explicit flag.
*Known limitation:* this reads the **sender's** clock, which is the wrong
question for a list in another hemisphere. It gets overridden routinely, and a
guard that is routinely overridden is the shape of the next incident. The right
version is recipient-aware.

**A four-layer blocklist that fails closed.** Anything unparseable is blocked
rather than allowed. Layer 4 re-checks immediately before each individual API
call, not once at startup, because a batch can be mutated in between.

**Suppression by domain, not address.** Someone who asked to be left alone did
not mean "write to my colleague instead".

**Identity binding.** Each sending identity has its own credential file. The
program reads which mailbox actually owns the credential and **refuses to run**
if that disagrees with the From header. Without this, a missing token silently
falls through to whichever one is present and sends the wrong copy from the wrong
address.

**A typed confirmation.** Before any real send, the subject and word count are
printed and a literal `YES` must be typed. This exists because 54 emails once
went out carrying the wrong template, and a two-second read of the subject line
would have caught it.

**A circuit breaker.** Stop the campaign if the failure rate passes 4%. A batch
of dead addresses halts itself after roughly one bounce in twenty-five.

## Resume-safe

Re-running after any stop picks up exactly where it left off, because the log is
the source of truth rather than a position in a file. Crash recovery and the
daily cap are the same mechanism.

## Pace like a person

Randomised gaps skewed short, with roughly one longer break in six. A uniform
spread is itself a signature: every gap landing inside one narrow band is not how
any human works.
