"""The guards are the safety-critical part, so they are the part with tests.

Each test below corresponds to a way this has actually gone wrong or could.
"""
import unittest

from src.guards import allowance, is_blocked, ramp_cap, should_stop
from src.angles import pick, seed_for
from src.classify import classify


class TestBlocklist(unittest.TestCase):
    def test_allows_a_real_person(self):
        self.assertIsNone(is_blocked("alex.chen@vendor.io"))

    def test_fails_closed_on_junk(self):
        # The default answer for anything unrecognisable is "do not send".
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
    def test_ceiling_climbs_and_then_holds(self):
        self.assertEqual(ramp_cap(1), 10)
        self.assertEqual(ramp_cap(4), 15)
        self.assertEqual(ramp_cap(10), 25)
        self.assertEqual(ramp_cap(500), 25)   # never above the top of the table

    def test_daily_cap_can_lower_but_never_raise(self):
        self.assertEqual(allowance(4, 0, 5), 5)     # lower: honoured
        self.assertEqual(allowance(4, 0, 99), 15)   # raise: ignored

    def test_second_run_of_the_same_command_sends_nothing(self):
        # This is the exact bug that produced 470 emails in one day.
        self.assertEqual(allowance(4, 15, 15), 0)

    def test_allowance_never_goes_negative(self):
        self.assertEqual(allowance(1, 999, 10), 0)


class TestCircuitBreaker(unittest.TestCase):
    def test_does_not_trip_on_a_small_sample(self):
        stop, _ = should_stop(10, 3)          # 30%, but only 10 attempts
        self.assertFalse(stop)

    def test_trips_above_the_threshold(self):
        stop, _ = should_stop(100, 9)
        self.assertTrue(stop)

    def test_holds_below_the_threshold(self):
        stop, _ = should_stop(100, 2)
        self.assertFalse(stop)


class TestClassifier(unittest.TestCase):
    def test_passes_a_product_vendor(self):
        v, _, cat = classify("Northwind", "Attack surface management platform for security teams.")
        self.assertEqual(v, "PASS")
        self.assertEqual(cat, "Exposure / CTEM")

    def test_rejects_a_reseller_even_with_security_words(self):
        v, _, _ = classify("Alder", "Value-added reseller for leading cybersecurity platforms.")
        self.assertEqual(v, "REJECT")

    def test_rejects_a_non_security_product(self):
        v, _, _ = classify("Orbit", "Logistics software platform with a dashboard and API.")
        self.assertEqual(v, "REJECT")

    def test_flags_product_plus_services_rather_than_guessing(self):
        v, _, _ = classify("Brightmoor", "Managed services, plus our own XDR platform and sensor.")
        self.assertEqual(v, "CHECK")


class TestAngles(unittest.TestCase):
    def test_choice_is_deterministic_in_the_address(self):
        a = pick("Identity / IAM", seed_for("x@y.io"))
        b = pick("Identity / IAM", seed_for("X@Y.IO  "))
        self.assertEqual(a, b)

    def test_subject_is_never_repeated_in_the_giveaway(self):
        primary, rest = pick("Cloud / CNAPP", seed_for("a@b.io"))
        self.assertNotIn(primary, rest)
        self.assertEqual(len(rest), 2)

    def test_unknown_category_falls_back_instead_of_raising(self):
        primary, rest = pick("Nonsense", 7)
        self.assertTrue(primary and len(rest) == 2)


if __name__ == "__main__":
    unittest.main()
