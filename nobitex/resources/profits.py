"""
Profit / Loss (Portfolio) endpoints – beta feature.

Provides daily profit & loss for the past week (or month) and aggregate totals.
All methods require authentication.
"""

from __future__ import annotations

from typing import Any, Dict


class Profits:
    """User profit/loss reports (beta)."""

    def __init__(self, client) -> None:
        self._client = client

    def get_last_week_daily_profit(self, monthly: bool = False) -> Dict[str, Any]:
        """
        Daily profit/loss for each of the last 7 days (or 30 days if ``monthly=True``).

        Args:
            monthly: If ``True``, returns data for the last 30 days instead of 7.

        Returns:
            ``{"status": "ok", "data": [{"report_date": ..., "total_profit": ..., "total_profit_percentage": ..., "total_balance": ...}, ...]}``

            May return ``{"status": "failed", "code": "PortfolioDisabled", ...}`` if the
            feature is not enabled for the account.
        """
        payload: Dict[str, Any] = {}
        if monthly:
            payload["monthly"] = True
        return self._client.post(
            "/users/portfolio/last-week-daily-profit",
            json=payload or None,
        )

    def get_last_week_daily_total_profit(self) -> Dict[str, Any]:
        """
        Total daily profit/loss (cumulative) for the last 7 days.

        Returns:
            ``{"status": "ok", "data": [{"report_date": ..., "total_profit": ..., "total_profit_percentage": ...}, ...]}``
        """
        return self._client.post("/users/portfolio/last-week-daily-total-profit")

    def get_last_month_total_profit(self) -> Dict[str, Any]:
        """
        Overall profit/loss and percentage for the last month.

        Returns:
            ``{"status": "ok", "data": {"total_profit": "...", "total_profit_percentage": "..."}}``
        """
        return self._client.post("/users/portfolio/last-month-total-profit")
