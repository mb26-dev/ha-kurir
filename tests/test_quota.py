"""Quota period tests that run without Home Assistant (python3 -m unittest discover tests)."""

import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "kurir_quota", Path(__file__).resolve().parents[1] / "custom_components" / "kurir" / "quota.py"
)
quota = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quota)


class TestQuotaPeriod(unittest.TestCase):
    def test_reset_day_23(self):
        from datetime import date
        qs, qe = quota.quota_period_start, quota.quota_period_end
        self.assertEqual(qs(date(2026, 11, 23), 23), date(2026, 11, 23))
        self.assertEqual(qs(date(2026, 11, 22), 23), date(2026, 10, 23))
        self.assertEqual(qs(date(2026, 12, 1), 23), date(2026, 11, 23))
        self.assertEqual(qe(date(2026, 11, 23), 23), date(2026, 12, 23))

    def test_calendar_month_and_year_change(self):
        from datetime import date
        qs, qe = quota.quota_period_start, quota.quota_period_end
        self.assertEqual(qs(date(2026, 11, 23), 1), date(2026, 11, 1))
        self.assertEqual(qs(date(2027, 1, 5), 23), date(2026, 12, 23))
        self.assertEqual(qe(date(2026, 12, 23), 23), date(2027, 1, 23))

    def test_short_months(self):
        from datetime import date
        qs, qe = quota.quota_period_start, quota.quota_period_end
        self.assertEqual(qs(date(2027, 2, 28), 31), date(2027, 2, 28))
        self.assertEqual(qs(date(2027, 2, 27), 31), date(2027, 1, 31))
        self.assertEqual(qe(date(2027, 1, 31), 31), date(2027, 2, 28))


if __name__ == "__main__":
    unittest.main()
