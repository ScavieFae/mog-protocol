"""Tests for txlog and surge pricing."""

from datetime import datetime, timezone, timedelta

from src.txlog import TransactionLog, _parse_ts
from src import pricing as pricing_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _old_iso(minutes_ago):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


# ---------------------------------------------------------------------------
# TransactionLog tests
# ---------------------------------------------------------------------------

def test_log_and_get_recent():
    log = TransactionLog()
    log.log({"service_id": "svc1", "timestamp": _now_iso(), "success": True})
    log.log({"service_id": "svc2", "timestamp": _now_iso(), "success": True})
    recent = log.get_recent(10)
    assert len(recent) == 2
    assert recent[-1]["service_id"] == "svc2"


def test_get_recent_truncates():
    log = TransactionLog()
    for i in range(10):
        log.log({"service_id": "svc", "timestamp": _now_iso()})
    assert len(log.get_recent(3)) == 3


def test_count_calls_in_window():
    log = TransactionLog()
    for _ in range(5):
        log.log({"service_id": "svc", "timestamp": _now_iso()})
    # Old entry outside window
    log.log({"service_id": "svc", "timestamp": _old_iso(30)})
    assert log.count_calls("svc", window_minutes=15) == 5


def test_count_calls_different_services():
    log = TransactionLog()
    log.log({"service_id": "svc_a", "timestamp": _now_iso()})
    log.log({"service_id": "svc_a", "timestamp": _now_iso()})
    log.log({"service_id": "svc_b", "timestamp": _now_iso()})
    assert log.count_calls("svc_a", window_minutes=15) == 2
    assert log.count_calls("svc_b", window_minutes=15) == 1
    assert log.count_calls("svc_c", window_minutes=15) == 0


def test_count_calls_empty_log():
    log = TransactionLog()
    assert log.count_calls("anything", window_minutes=15) == 0


def test_parse_ts_bad_value():
    # Should return epoch, not raise
    dt = _parse_ts("not-a-date")
    assert dt.timestamp() == 0.0


# ---------------------------------------------------------------------------
# Pricing tests (use isolated txlog to avoid global state)
# ---------------------------------------------------------------------------

def _make_pricing(n_calls, service_id="test_svc"):
    """Return (price, multiplier) after logging n_calls into a fresh txlog."""
    log = TransactionLog()
    for _ in range(n_calls):
        log.log({"service_id": service_id, "timestamp": _now_iso()})

    # Temporarily patch the module-level txlog used by pricing
    original = pricing_module.txlog
    pricing_module.txlog = log
    try:
        result = pricing_module.get_current_price(service_id, base_price=10)
    finally:
        pricing_module.txlog = original
    return result


def test_pricing_baseline():
    price, mult = _make_pricing(0)
    assert mult == 1.0
    assert price == 10


def test_pricing_medium_tier():
    # Just at medium threshold (default 10)
    price, mult = _make_pricing(10)
    assert mult == 1.5
    assert price == 15


def test_pricing_below_medium():
    price, mult = _make_pricing(9)
    assert mult == 1.0
    assert price == 10


def test_pricing_high_tier():
    # Just at high threshold (default 20)
    price, mult = _make_pricing(20)
    assert mult == 2.0
    assert price == 20


def test_pricing_below_high():
    price, mult = _make_pricing(19)
    assert mult == 1.5
    assert price == 15


def test_pricing_surge_ignores_old_calls():
    """Calls outside the 15-min window must not trigger surge."""
    log = TransactionLog()
    # Add 25 old calls — should be ignored
    for _ in range(25):
        log.log({"service_id": "svc", "timestamp": _old_iso(30)})
    # Add 3 recent calls — baseline tier
    for _ in range(3):
        log.log({"service_id": "svc", "timestamp": _now_iso()})

    original = pricing_module.txlog
    pricing_module.txlog = log
    try:
        price, mult = pricing_module.get_current_price("svc", base_price=10)
    finally:
        pricing_module.txlog = original

    assert mult == 1.0
    assert price == 10


# ---------------------------------------------------------------------------
# Integration: volume builds → price escalates
# ---------------------------------------------------------------------------

def test_price_escalates_with_volume():
    log = TransactionLog()

    original = pricing_module.txlog
    pricing_module.txlog = log
    try:
        # Initially baseline
        p0, m0 = pricing_module.get_current_price("svc", 10)
        assert m0 == 1.0

        # Log 10 calls → medium
        for _ in range(10):
            log.log({"service_id": "svc", "timestamp": _now_iso()})
        p1, m1 = pricing_module.get_current_price("svc", 10)
        assert m1 == 1.5

        # Log 10 more → high (20 total)
        for _ in range(10):
            log.log({"service_id": "svc", "timestamp": _now_iso()})
        p2, m2 = pricing_module.get_current_price("svc", 10)
        assert m2 == 2.0
    finally:
        pricing_module.txlog = original


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_log_and_get_recent,
        test_get_recent_truncates,
        test_count_calls_in_window,
        test_count_calls_different_services,
        test_count_calls_empty_log,
        test_parse_ts_bad_value,
        test_pricing_baseline,
        test_pricing_medium_tier,
        test_pricing_below_medium,
        test_pricing_high_tier,
        test_pricing_below_high,
        test_pricing_surge_ignores_old_calls,
        test_price_escalates_with_volume,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)
