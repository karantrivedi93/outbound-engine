"""Choose the subject line for an account, from the loaded profile.

No market knowledge lives here. The angles themselves are in `profiles/*.json`;
this is only the selection rule, which is the same whatever you sell.

THREE ANGLES PER SEGMENT, ALWAYS

The subject takes one and the body gives away the other two. Giving them away
costs nothing and makes the email useful to someone who never replies, which is
most people. `src/profile.py` refuses to load a profile where any segment has a
different number, because losing one silently degrades every email in the batch
with no error anywhere.
"""


def pick(profile, segment, seed):
    """Return (subject, [the two not used]).

    Deterministic in the recipient's address. Seeding on the address rather than
    a counter means the same person always gets the same line, a rebuild is
    reproducible, and the choice survives the list being re-sorted or filtered.
    It spreads the three angles evenly across a batch with no state at all.
    """
    angles = profile.angles.get(segment)
    if not angles:
        angles = profile.angles[profile.segments[-1][0]]
    primary = angles[seed % len(angles)]
    return primary, [a for a in angles if a != primary]


def seed_for(email):
    return sum(ord(c) for c in email.strip().lower())
