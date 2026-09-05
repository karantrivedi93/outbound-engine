"""Tests for the parts where being wrong is expensive.

Each test corresponds to a way this has actually gone wrong, or a property the
pipeline silently depends on.
"""
import unittest

from src.angles import ANGLES, pick, seed_for
from src.classify import classify
from src.compose import compose
from src.guards import allowance, is_blocked, ramp_cap, should_stop


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


class TestQualification(unittest.TestCase):
    def test_incumbent_and_scale_is_tier_one(self):
        v, tier, _seg, _why = classify(
            "Meridian", "Kubernetes across three regions, Datadog bill grew 40%.", 140)
        self.assertEqual((v, tier), ("PASS", 1))

    def test_plural_architecture_words_still_count(self):
        # \\bmicroservice\\b does not match "microservices", which is how every
        # engineering blog on earth actually writes it.
        v, _t, _s, _w = classify("Orbit", "Microservices on ECS, using Datadog.", 110)
        self.assertEqual(v, "PASS")

    def test_otel_alone_qualifies_without_an_architecture_word(self):
        # The warmest possible account must not be rejected for failing to say
        # "microservices". OTLP in production IS the scale evidence.
        v, tier, _s, _w = classify(
            "Lumen", "E-commerce platform migrating tracing off New Relic with "
                     "OpenTelemetry collectors.", 320)
        self.assertEqual((v, tier), ("PASS", 1))

    def test_hiring_only_is_tier_two_not_tier_one(self):
        v, tier, _s, _w = classify(
            "Draftsmith", "Event-driven inference pipeline. Hiring a platform "
                          "engineer to own reliability.", 45)
        self.assertEqual((v, tier), ("PASS", 2))

    def test_competitor_is_rejected(self):
        v, _t, _s, _w = classify(
            "Sentinel", "We provide monitoring: an observability platform with "
                        "APM for distributed systems.", 55)
        self.assertEqual(v, "REJECT")

    def test_agency_is_rejected_despite_kubernetes(self):
        v, _t, _s, _w = classify(
            "Vantage", "Digital agency delivering Kubernetes and observability "
                       "tooling for clients.", 80)
        self.assertEqual(v, "REJECT")

    def test_no_trigger_is_nurture_not_reject(self):
        # Deleting these from the list is permanent. They are simply not this
        # week's work.
        v, _t, _s, _w = classify("Northwind", "Fleet tracking on k8s with autoscaling.", 90)
        self.assertEqual(v, "CHECK")

    def test_too_small_has_no_budget(self):
        v, _t, _s, _w = classify("Tinsmith", "Containers, using Datadog.", 6)
        self.assertEqual(v, "REJECT")

    def test_enterprise_is_a_different_motion(self):
        v, tier, _s, _w = classify(
            "Halden", "Microservices on Kubernetes, on Dynatrace and Splunk.", 4200)
        self.assertEqual((v, tier), ("CHECK", 3))

    def test_every_verdict_carries_its_evidence(self):
        for args in [("A", "Microservices, Datadog.", 100), ("B", "A law firm.", 50)]:
            _v, _t, _s, reasons = classify(*args)
            self.assertTrue(reasons and all(r.strip() for r in reasons))


class TestAngles(unittest.TestCase):
    def test_every_segment_has_exactly_three_angles(self):
        # compose() gives away the two the subject did not use.
        for name, angles in ANGLES.items():
            self.assertEqual(len(angles), 3, f"{name} has {len(angles)}")
            self.assertEqual(len(set(angles)), 3, f"{name} repeats an angle")

    def test_choice_is_deterministic_in_the_address(self):
        self.assertEqual(pick("Cardinality", seed_for("x@y.io")),
                         pick("Cardinality", seed_for("X@Y.IO  ")))

    def test_subject_is_never_repeated_in_the_giveaway(self):
        primary, rest = pick("Vendor lock-in", seed_for("a@b.io"))
        self.assertNotIn(primary, rest)
        self.assertEqual(len(rest), 2)

    def test_unknown_segment_falls_back_instead_of_raising(self):
        primary, rest = pick("Nonsense", 7)
        self.assertTrue(primary and len(rest) == 2)


class TestCopy(unittest.TestCase):
    def test_stays_inside_the_word_budget(self):
        _s, body = compose("Priya", "priya@a.example", "Acme", "Cost / bill growth")
        self.assertLessEqual(len(body.split()), 80)

    def test_no_marketing_adjectives_survive(self):
        # These words are the fastest way to lose a technical reader.
        banned = ["powerful", "seamless", "revolutionary", "best-in-class",
                  "cutting-edge", "game-changing", "synergy", "leverage"]
        for segment in ANGLES:
            _s, body = compose("A", f"a@{segment[:3].lower()}.example", "Co", segment)
            for word in banned:
                self.assertNotIn(word, body.lower(), f"{word!r} in {segment}")

    def test_bodies_differ_across_recipients(self):
        seen = {compose("A", f"user{i}@x.example", "Co", "Tool sprawl")[1]
                for i in range(6)}
        self.assertGreater(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
