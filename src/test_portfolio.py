"""Tests for PortfolioManager."""

import json
import os
import tempfile

import pytest

from src.portfolio import PortfolioManager


@pytest.fixture
def pm(tmp_path):
    """Fresh PortfolioManager backed by a temp file."""
    return PortfolioManager(path=str(tmp_path / "portfolio.json"), starting_credits=50)


def test_fresh_balance(pm):
    assert pm.balance == 50


def test_earn_updates_balance(pm):
    pm.earn(10, "svc_a", "test revenue")
    assert pm.balance == 60


def test_spend_updates_balance(pm):
    pm.spend(20, "svc_a", "test cost")
    assert pm.balance == 30


def test_spend_over_budget_returns_false(pm):
    result = pm.spend(100, "svc_a", "too much")
    assert result is False
    assert pm.balance == 50


def test_spend_over_budget_unchanged(pm):
    pm.spend(100, "svc_a", "too much")
    assert pm.balance == 50


def test_propose_creates_hypothesis(pm):
    hyp_id = pm.propose("svc_b", "Will sell well", 20, 2)
    assert hyp_id == "hyp-001"
    hyps = pm.get_active_hypotheses()
    assert len(hyps) == 1
    h = hyps[0]
    assert h["service_id"] == "svc_b"
    assert h["status"] == "proposed"
    assert h["expected_revenue"] == 20
    assert h["cost_to_validate"] == 2
    assert h["actual_revenue"] == 0


def test_record_sale_updates_pnl_and_hypothesis(pm):
    pm.propose("svc_c", "Revenue test", 30, 1)
    pm.record_sale("svc_c", 5)
    assert pm.balance == 55
    hyps = pm.get_active_hypotheses()
    assert hyps[0]["actual_revenue"] == 5


def test_should_invest_true(pm):
    assert pm.should_invest(cost=10, expected_revenue=25) is True


def test_should_invest_false_roi(pm):
    # expected_revenue < 2 * cost
    assert pm.should_invest(cost=10, expected_revenue=15) is False


def test_should_invest_false_budget(pm):
    pm.spend(45, "svc_x", "drain budget")
    # balance = 5, cost = 10
    assert pm.should_invest(cost=10, expected_revenue=30) is False


def test_roi_zero_when_nothing_spent(pm):
    assert pm.roi == 0.0


def test_roi_calculation(pm):
    pm.spend(10, "svc_a", "cost")
    pm.earn(25, "svc_a", "revenue")
    assert pm.roi == pytest.approx((25 - 10) / 10)


def test_json_persistence(tmp_path):
    path = str(tmp_path / "portfolio.json")
    pm1 = PortfolioManager(path=path, starting_credits=50)
    pm1.spend(10, "svc_a", "cost")
    pm1.earn(20, "svc_b", "revenue")
    pm1.propose("svc_c", "test", 40, 5)

    pm2 = PortfolioManager(path=path, starting_credits=50)
    assert pm2.balance == 60
    assert len(pm2.get_active_hypotheses()) == 1
    assert pm2.roi == pytest.approx((20 - 10) / 10)


def test_get_best_performers(pm):
    pm.propose("svc_a", "a", 10, 1)
    pm.propose("svc_b", "b", 20, 2)
    pm.record_sale("svc_a", 15)
    pm.record_sale("svc_b", 5)
    top = pm.get_best_performers(top_k=1)
    assert top[0]["service_id"] == "svc_a"


def test_terminal_hypotheses_excluded_from_active(pm):
    hyp_id = pm.propose("svc_d", "test", 10, 1)
    pm.update_hypothesis(hyp_id, "killed")
    assert pm.get_active_hypotheses() == []


def test_get_summary_keys(pm):
    summary = pm.get_summary()
    for key in ("balance", "total_spent", "total_earned", "roi", "active_hypotheses", "top_earner"):
        assert key in summary
