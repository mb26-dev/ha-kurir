"""eTrackings quota period (pure functions, no Home Assistant imports)."""

from __future__ import annotations

import calendar
from datetime import date


def quota_period_start(today: date, reset_day: int) -> date:
    """First day of the current eTrackings quota period.

    The quota renews every month on ``reset_day`` (the day the account was
    created). In months shorter than ``reset_day`` it renews on the last day.
    """
    reset_day = max(1, min(31, int(reset_day)))

    def renew_day(year: int, month: int) -> date:
        last = calendar.monthrange(year, month)[1]
        return date(year, month, min(reset_day, last))

    this_month = renew_day(today.year, today.month)
    if today >= this_month:
        return this_month
    year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return renew_day(year, month)


def quota_period_end(start: date, reset_day: int) -> date:
    """Day the quota period that began on ``start`` renews."""
    reset_day = max(1, min(31, int(reset_day)))
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    return date(year, month, min(reset_day, calendar.monthrange(year, month)[1]))
