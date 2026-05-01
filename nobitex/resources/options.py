"""
System‑wide configuration and market settings (public).

The /v2/options endpoint returns active currencies, network information,
precision rules, withdrawal limits, and feature flags. No authentication
is required to call it.
"""

from __future__ import annotations

from typing import Any, Dict


class Options:
    """System configuration (public)."""

    def __init__(self, client) -> None:
        """
        Args:
            client: A ``nobitex.Client`` instance (authentication is optional
                for this endpoint).
        """
        self._client = client

    def get(self) -> Dict[str, Any]:
        """
        Retrieve the full system options dictionary.

        Returns a large JSON object with the following top‑level keys:

        - ``features`` – enabled flags and beta features
        - ``coins`` – list of currencies, each with network‑specific settings
        - ``nobitex`` – global market parameters (min orders, precisions,
          withdrawal limits, etc.)

        Example::

            options = Options(client).get()
            btc_networks = next(
                coin["networkList"] for coin in options["coins"] if coin["coin"] == "btc"
            )
            print(btc_networks.keys())
        """
        return self._client.get("/v2/options")
