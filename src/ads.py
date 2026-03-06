"""Ad-supported free tier — contextual ads appended to free-plan responses.

Mock mode (ADS_MOCK=true) provides deterministic test ads.
With CHATADS_API_KEY set, fetches real contextual ads from ChatAds.
Without either, returns None (no ads, graceful degradation).
"""

import os
from typing import Optional

import httpx

CHATADS_API_KEY = os.getenv("CHATADS_API_KEY")


def get_contextual_ad(query: str, context: str = "") -> Optional[dict]:
    """Fetch a contextual ad. Returns None on failure or missing config.
    3-second timeout — never blocks the main response.
    """
    if CHATADS_API_KEY:
        try:
            resp = httpx.post(
                "https://api.getchatads.com/v1/ads",
                headers={"Authorization": f"Bearer {CHATADS_API_KEY}"},
                json={"query": query, "context": context, "format": "text"},
                timeout=3,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "label": "Sponsored",
                    "text": data.get("text", ""),
                    "url": data.get("url", ""),
                    "sponsor": data.get("advertiser", ""),
                }
        except Exception:
            pass
        return None

    if os.getenv("ADS_MOCK"):
        return _mock_ad(query)

    return None


def _mock_ad(query: str) -> dict:
    """Deterministic mock ad for testing."""
    return {
        "label": "Sponsored (mock)",
        "text": f"Explore more tools related to '{query}' at the Nevermined marketplace",
        "url": "https://nevermined.app",
        "sponsor": "Nevermined",
    }
