"""Multi-signal surge pricing: volume tier + demand pressure + velocity + cooldown."""

import os
import time
from datetime import datetime, timezone

from src.telemetry import telemetry
from src.txlog import txlog, _parse_ts

SURGE_THRESHOLD_HIGH = int(os.getenv("SURGE_THRESHOLD_HIGH", "20"))
SURGE_THRESHOLD_MEDIUM = int(os.getenv("SURGE_THRESHOLD_MEDIUM", "10"))

# Per-service surge state for cooldown tracking
_surge_state: dict[str, dict] = {}
# {"exa_search": {"last_multiplier": 1.5, "last_updated": 1234567.0, "peak_multiplier": 2.0}}


def _volume_tier(service_id: str) -> float:
    """Base tier from 15-minute rolling call count."""
    recent = telemetry.count_calls(service_id, window_minutes=15)
    if recent >= SURGE_THRESHOLD_HIGH:
        return 2.0
    elif recent >= SURGE_THRESHOLD_MEDIUM:
        return 1.5
    return 1.0


def _velocity(service_id: str) -> float:
    """Ratio of recent call rate (5m) to baseline (15m). >1.5 = accelerating."""
    count_5m = telemetry.count_calls(service_id, window_minutes=5)
    count_15m = telemetry.count_calls(service_id, window_minutes=15)
    if count_15m == 0:
        return 1.0
    rate_5m = count_5m / 5.0
    rate_15m = count_15m / 15.0
    if rate_15m == 0:
        return 1.0
    return rate_5m / rate_15m


def _demand_pressure(service_id: str) -> float:
    """Ratio of searches mentioning this service to actual purchases in last 15m.

    >2.0 = high latent demand (people looking but not buying).
    Returns 1.0 when no search data, 1.1 when searches exist but no purchases yet.
    """
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 15 * 60
    entries = txlog.get_recent(500)

    # Match by service_id keywords (split on underscore, skip short tokens)
    keywords = [w for w in service_id.split("_") if len(w) > 3]
    full_phrase = service_id.replace("_", " ").lower()

    def _query_matches(query: str) -> bool:
        q = query.lower()
        return full_phrase in q or any(k in q for k in keywords)

    searches = sum(
        1
        for e in entries
        if e.get("event_type") in ("find_service", "unmet_demand")
        and _parse_ts(e.get("timestamp", "")).timestamp() >= cutoff
        and _query_matches(e.get("query", ""))
    )
    purchases = telemetry.count_calls(service_id, window_minutes=15)

    if searches == 0:
        return 1.0
    if purchases == 0:
        return 1.1  # Searches but no buys yet = latent demand
    return min(searches / purchases, 2.0)


def _cooldown_multiplier(service_id: str, base_mult: float) -> float:
    """Smooth decay: hold price up after surge drop, stepping down 0.1x per 2 minutes.

    Returns a ratio >= 1.0 that keeps prices elevated during cooldown.
    Returns 1.0 when not in cooldown (price rising or stable).
    """
    state = _surge_state.get(service_id, {})
    last_mult = state.get("last_multiplier", 1.0)
    last_time = state.get("last_updated", 0.0)

    if base_mult >= last_mult:
        # Not in cooldown — price is rising or holding
        return 1.0

    elapsed_minutes = (time.time() - last_time) / 60.0
    steps = elapsed_minutes / 2.0  # one step every 2 minutes
    decayed = last_mult - steps * 0.1
    decayed = max(decayed, base_mult)  # floor at current volume tier

    if base_mult > 0:
        return decayed / base_mult  # ratio to boost base_mult up to the cooldown floor
    return 1.0


def get_surge_info(service_id: str, base_price: int) -> dict:
    """Compute full surge info. Returns price, multiplier, and per-signal breakdown.

    Also updates _surge_state for cooldown tracking.
    """
    base_mult = _volume_tier(service_id)
    vel = _velocity(service_id)
    demand = _demand_pressure(service_id)
    cooldown = _cooldown_multiplier(service_id, base_mult)

    demand_boost = min(demand, 1.2)
    velocity_boost = min(vel, 1.3)

    final = base_mult * demand_boost * velocity_boost * cooldown
    final = max(1.0, min(final, 3.0))  # floor 1.0, cap 3.0

    # Trend vs last known multiplier
    state = _surge_state.get(service_id, {})
    last_mult = state.get("last_multiplier", 1.0)
    if final > last_mult + 0.05:
        trend = "rising"
    elif final < last_mult - 0.05:
        trend = "falling"
    else:
        trend = "stable"

    # Update state for next call's cooldown calculation
    _surge_state[service_id] = {
        "last_multiplier": final,
        "last_updated": time.time(),
        "peak_multiplier": max(final, state.get("peak_multiplier", 1.0)),
    }

    count_15m = telemetry.count_calls(service_id, window_minutes=15)

    return {
        "price": int(base_price * final),
        "surge_multiplier": round(final, 3),
        "surge_signals": {
            "volume_15m": count_15m,
            "velocity": round(vel, 3),
            "demand_pressure": round(demand, 3),
            "trend": trend,
        },
    }


def get_current_price(service_id: str, base_price: int) -> tuple[int, float]:
    """Return (price, surge_multiplier). Signature unchanged for existing callers."""
    info = get_surge_info(service_id, base_price)
    return info["price"], info["surge_multiplier"]
