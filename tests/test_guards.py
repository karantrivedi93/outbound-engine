"""Tests for the parts where being wrong is expensive.

Each test corresponds to a way this has gone wrong, or a property the pipeline
silently depends on. The profile tests run over EVERY shipped profile, so adding
a market cannot ship a broken one.
"""
import unittest

from src import profile as profile_mod
from src.angles import pick, seed_for
from src.classify import classify, segment
from src.compose import compose
from src.guards import allowance, is_blocked, ramp_cap, should_stop

OBS = profile_mod.load("observability")
SEC = profile_mod.load("security")


class TestBlocklist(unittest.TestCase):
    def test_allows_a_real_person(self):
        self.assertIsNone(is_blocked("priya@meridianpay.example"))

    def test_fails_closed_on_junk(self):
        for bad in ["", None, "not-an-email", "no@domain", "@nolocal.com", 42]:
            self.assertIsNotNone(is_blocked(bad), f"should have blocked {bad!r}")

    def test_blocks_role_and_reserved_addresses(self):
        for addr in ["info@v.io", "sales@v.io", "abuse@v.io", "postmaster@v.io"]:
            self.assertIsNotNone(is_blocked(addr))

    def test_suppression_is_by_domain_not_address(self):
        # Someone who asked to be left alone did not mean "email my colleague".
        self.assertIsNotNone(is_blocked("someone.else@quiet.io", {"quiet.io"}))

    def test_case_and_whitespace_do_not_evade(self):
        self.assertIsNotNone(is_blocked("  INFO@Vendor.IO  "))


class TestRamp(unittest.TestCase):
    def test_ceiling_climbs_then_holds(self):
        self.assertEqual(ramp_cap(1), 10)
        self.assertEqual(ramp_cap(4), 15)
        self.assertEqual(ramp_cap(500), 25)

    def test_daily_cap_can_lower_but_never_raise(self):
        self.assertEqual(allowance(4, 0, 5), 5)
        self.assertEqual(allowance(4, 0, 99), 15)

    def test_second_run_of_the_same_command_sends_nothing(self):
        # The exact bug that produced 470 emails in one day.
        self.assertEqual(allowance(4, 15, 15), 0)

    def test_allowance_never_goes_negative(self):
        self.assertEqual(allowance(1, 999, 10), 0)


class TestCircuitBreaker(unittest.TestCase):
    def test_ignores_a_small_sample(self):
        self.assertFalse(should_stop(10, 3)[0])

    def test_trips_above_threshold(self):
        self.assertTrue(should_stop(100, 9)[0])

    def test_holds_below_threshold(self):
        self.assertFalse(should_stop(100, 2)[0])


class TestProfiles(unittest.TestCase):
    """Run over every shipped profile. Adding a market runs these for free."""

    def test_at_least_two_markets_ship(self):
        # One profile proves nothing about generality.
        self.assertGreaterEqual(len(profile_mod.available()), 2)

    def test_every_profile_loads(self):
        for name in profile_mod.available():
            self.assertTrue(profile_mod.load(name).market)

    def test_every_segment_has_exactly_three_angles(self):
        # compose() gives away the two the subject did not use.
        for name in profile_mod.available():
            p = profile_mod.load(name)
            for seg_name, _pattern in p.segments:
                angles = p.angles[seg_name]
                self.assertEqual(len(angles), 3, f"{name}/{seg_name}")
                self.assertEqual(len(set(angles)), 3, f"{name}/{seg_name} repeats")

    def test_every_trigger_has_a_tier_and_a_reason(self):
        for name in profile_mod.available():
            for t in profile_mod.load(name).triggers:
                self.assertIn(t["tier"], (1, 2, 3))
                self.assertTrue(t["why"].strip())

    def test_mechanism_lines_accept_the_product_placeholder(self):
        for name in profile_mod.available():
            for line in profile_mod.load(name).mechanism:
                self.assertIn("{product}", line, f"{name}: {line[:40]}")

    def test_a_broken_profile_is_refused_at_load(self):
        for bad in ["does-not-exist", "/tmp/nope.json"]:
            with self.assertRaises(profile_mod.ProfileError):
                profile_mod.load(bad)


class TestQualification(unittest.TestCase):
    def test_incumbent_and_scale_is_tier_one(self):
        v, tier, _s, _w = classify(
            OBS, "Meridian", "Kubernetes across three regions, Datadog bill grew 40%.", 140)
        self.assertEqual((v, tier), ("PASS", 1))

    def test_plural_architecture_words_still_count(self):
        # \\bmicroservice\\b does not match "microservices", which is how every
        # engineering blog on earth actually writes it.
        v, _t, _s, _w = classify(OBS, "Orbit", "Microservices on ECS, using Datadog.", 110)
        self.assertEqual(v, "PASS")

    def test_trigger_alone_qualifies_without_an_architecture_word(self):
        # The warmest account must not be rejected for failing to say the magic
        # word. OTLP in production IS the scale evidence.
        v, tier, _s, _w = classify(
            OBS, "Lumen", "E-commerce platform migrating tracing off New Relic "
                          "with OpenTelemetry collectors.", 320)
        self.assertEqual((v, tier), ("PASS", 1))

    def test_hiring_only_is_tier_two(self):
        v, tier, _s, _w = classify(
            OBS, "Draftsmith", "Event-driven inference pipeline. Hiring a platform "
                               "engineer to own reliability.", 45)
        self.assertEqual((v, tier), ("PASS", 2))

    def test_competitor_is_rejected(self):
        v, _t, _s, _w = classify(
            OBS, "Sentinel", "We provide monitoring: an observability platform "
                             "with APM for distributed systems.", 55)
        self.assertEqual(v, "REJECT")

    def test_no_trigger_is_nurture_not_reject(self):
        # Rejecting deletes them permanently. They are not this week's work.
        v, _t, _s, _w = classify(OBS, "Northwind", "Fleet tracking on k8s with autoscaling.", 90)
        self.assertEqual(v, "CHECK")

    def test_size_band_comes_from_the_profile(self):
        # 60 is inside security's 10-500 and outside nothing; 3000 is outside
        # observability's 15-2000. The number is never hard-coded in the code.
        v, _t, _s, _w = classify(SEC, "Verity", "AppSec platform. Series A raised.", 60)
        self.assertEqual(v, "PASS")
        v, tier, _s, _w = classify(OBS, "Halden", "Microservices on k8s, on Dynatrace.", 3000)
        self.assertEqual((v, tier), ("CHECK", 3))

    def test_the_same_code_works_a_different_market(self):
        # The whole claim of the profile system, asserted.
        v, tier, seg, _w = classify(
            SEC, "Kestrel", "Identity security platform for privileged access. "
                            "Hiring a sales development rep.", 120)
        self.assertEqual((v, tier), ("PASS", 1))
        self.assertEqual(seg, "Identity / IAM")

    def test_every_verdict_carries_its_evidence(self):
        for args in [(OBS, "A", "Microservices, Datadog.", 100), (OBS, "B", "A law firm.", 50)]:
            _v, _t, _s, reasons = classify(*args)
            self.assertTrue(reasons and all(r.strip() for r in reasons))


class TestAngles(unittest.TestCase):
    def test_choice_is_deterministic_in_the_address(self):
        self.assertEqual(pick(OBS, "Cardinality", seed_for("x@y.io")),
                         pick(OBS, "Cardinality", seed_for("X@Y.IO  ")))

    def test_subject_is_never_repeated_in_the_giveaway(self):
        primary, rest = pick(OBS, "Vendor lock-in", seed_for("a@b.io"))
        self.assertNotIn(primary, rest)
        self.assertEqual(len(rest), 2)

    def test_unknown_segment_falls_back_instead_of_raising(self):
        primary, rest = pick(OBS, "Nonsense", 7)
        self.assertTrue(primary and len(rest) == 2)

    def test_most_specific_segment_wins(self):
        # segment() returns the first match, so a general pattern placed early
        # would swallow the specific ones. The segment picks the subject line.
        self.assertEqual(segment(OBS, "our LLM inference costs are rising"),
                         "AI / LLM workloads")


class TestCopy(unittest.TestCase):
    def test_stays_inside_the_word_budget(self):
        for p in (OBS, SEC):
            for seg_name, _ in p.segments:
                _s, body = compose(p, "Priya", "priya@a.example", "Acme", seg_name)
                self.assertLessEqual(len(body.split()), 85, f"{p.market}/{seg_name}")

    def test_no_marketing_adjectives_survive(self):
        # The fastest way to lose a technical reader, and it creeps back in.
        banned = ["powerful", "seamless", "revolutionary", "best-in-class",
                  "cutting-edge", "game-changing", "synergy", "leverage"]
        for p in (OBS, SEC):
            for seg_name, _ in p.segments:
                _s, body = compose(p, "A", f"a@{abs(hash(seg_name)) % 999}.example",
                                   "Co", seg_name)
                for word in banned:
                    self.assertNotIn(word, body.lower(), f"{word!r} in {seg_name}")

    def test_product_name_is_injected_not_hardcoded(self):
        _s, body = compose(OBS, "A", "a@x.example", "Co", "Cost / bill growth",
                           product="Zeppelin")
        self.assertIn("Zeppelin", body)

    def test_bodies_differ_across_recipients(self):
        seen = {compose(OBS, "A", f"user{i}@x.example", "Co", "Tool sprawl")[1]
                for i in range(6)}
        self.assertGreater(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
