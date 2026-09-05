"""Load and validate a market profile.

A profile is the whole definition of a target market: who to disqualify, what
counts as evidence of scale, which triggers make an account warm, which pain to
lead with, and the subject lines for each. Everything vertical-specific lives in
`profiles/*.json`; nothing outside that directory names a market or a product.

Retargeting the engine at a new market is writing one JSON file. That is the
claim this module exists to make true, and `--profile` on every entry point is
what keeps it honest: two shipped profiles sell into completely different
worlds through identical code.

VALIDATION IS LOUD AND AT LOAD TIME

A profile is data, and data written by hand is data with mistakes in it. Every
one of these has bitten a real run:

  * a segment with no angles           -> KeyError deep inside compose()
  * a segment with two angles          -> the giveaway line silently loses one
  * a bad regex                        -> re.error mid-batch, half the list sent
  * a trigger with no tier             -> account ranked None, sorted last

All of them are cheap to catch here and expensive to catch later, so the loader
refuses to return a broken profile rather than failing partway through a send.
"""
import json
import os
import re

REQUIRED = ("market", "product", "size_band", "disqualify",
            "scale_signal", "triggers", "segments", "angles")
HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(os.path.dirname(HERE), "profiles")


class ProfileError(ValueError):
    """A profile that would fail later, refused now."""


class Profile:
    def __init__(self, raw, path):
        self.path = path
        self.market = raw["market"]
        self.buyer = raw.get("buyer", "")
        self.notes = raw.get("notes", "")
        self.mechanism = raw["product"]["mechanism"]
        self.min_size, self.max_size = raw["size_band"]
        self.size_unit = raw.get("size_unit", "employees")
        self.disqualify = raw["disqualify"]
        self.scale_signal = raw["scale_signal"]
        self.triggers = raw["triggers"]
        self.segments = raw["segments"]
        self.angles = raw["angles"]

    def __repr__(self):
        return f"<Profile {os.path.basename(self.path)}: {self.market}>"


def _check_regex(pattern, where):
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ProfileError(f"{where}: bad regex {pattern!r} ({exc})")


def load(name_or_path):
    """Load by profile name ('observability') or by path."""
    path = name_or_path
    if not os.path.exists(path):
        path = os.path.join(PROFILE_DIR, f"{name_or_path}.json")
    if not os.path.exists(path):
        raise ProfileError(f"no profile {name_or_path!r}. Available: {', '.join(available())}")

    with open(path) as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ProfileError(f"{path}: invalid JSON ({exc})")

    missing = [k for k in REQUIRED if k not in raw]
    if missing:
        raise ProfileError(f"{path}: missing {', '.join(missing)}")

    for label, pattern in raw["disqualify"].items():
        _check_regex(pattern, f"{path}: disqualify.{label}")
    _check_regex(raw["scale_signal"], f"{path}: scale_signal")

    for t in raw["triggers"]:
        for field in ("name", "pattern", "why", "tier"):
            if field not in t:
                raise ProfileError(f"{path}: trigger {t.get('name', '?')!r} missing {field!r}")
        _check_regex(t["pattern"], f"{path}: trigger {t['name']}")

    seen = set()
    for entry in raw["segments"]:
        if len(entry) != 2:
            raise ProfileError(f"{path}: segment {entry!r} is not [name, pattern]")
        name, pattern = entry
        _check_regex(pattern, f"{path}: segment {name}")
        if name in seen:
            raise ProfileError(f"{path}: segment {name!r} listed twice")
        seen.add(name)
        # compose() takes one angle for the subject and gives the other two
        # away. Fewer than three breaks that quietly rather than loudly.
        angles = raw["angles"].get(name)
        if not angles:
            raise ProfileError(f"{path}: segment {name!r} has no angles")
        if len(angles) != 3:
            raise ProfileError(f"{path}: segment {name!r} has {len(angles)} angles, needs 3")
        if len(set(angles)) != 3:
            raise ProfileError(f"{path}: segment {name!r} repeats an angle")

    if not raw["product"].get("mechanism"):
        raise ProfileError(f"{path}: product.mechanism is empty")

    lo, hi = raw["size_band"]
    if lo >= hi:
        raise ProfileError(f"{path}: size_band {lo}-{hi} is inverted")

    return Profile(raw, path)


def available():
    if not os.path.isdir(PROFILE_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(PROFILE_DIR) if f.endswith(".json"))


if __name__ == "__main__":
    for name in available():
        p = load(name)
        print(f"{name:<16} {len(p.angles)} segments, {len(p.triggers)} triggers, "
              f"{p.min_size}-{p.max_size} {p.size_unit}")
        print(f"{'':<16} {p.market}")
