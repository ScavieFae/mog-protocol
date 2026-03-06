"""Three-tier surge pricing based on recent transaction volume."""

import os

from src.telemetry import telemetry

SURGE_THRESHOLD_HIGH = int(os.getenv("SURGE_THRESHOLD_HIGH", "20"))
SURGE_THRESHOLD_MEDIUM = int(os.getenv("SURGE_THRESHOLD_MEDIUM", "10"))


def get_current_price(service_id: str, base_price: int) -> tuple[int, float]:
    """Return (price, surge_multiplier) based on recent call volume.

    Tiers (rolling 15-minute window):
      >= SURGE_THRESHOLD_HIGH   → 2.0x
      >= SURGE_THRESHOLD_MEDIUM → 1.5x
      else                      → 1.0x
    """
    recent = telemetry.count_calls(service_id, window_minutes=15)
    if recent >= SURGE_THRESHOLD_HIGH:
        return int(base_price * 2.0), 2.0
    elif recent >= SURGE_THRESHOLD_MEDIUM:
        return int(base_price * 1.5), 1.5
    else:
        return base_price, 1.0
