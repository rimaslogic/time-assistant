from engine.config import TenantConfig, DEFAULT_FRAMEWORK
from modules import client_budget as cb


def _cfg(modules):
    return TenantConfig(tenant_id="t", name="n", timezone="UTC",
                        working_days=[], framework=DEFAULT_FRAMEWORK, modules=modules)


def test_is_enabled():
    assert cb.is_enabled(_cfg(["client_budget"])) is True
    assert cb.is_enabled(_cfg([])) is False


def test_resolve_budget_month_specific():
    c = {"allocated_hours": 2, "may_allocated_hours": 4, "june_allocated_hours": 8}
    assert cb.resolve_budget(c, "june") == 8


def test_resolve_budget_falls_back_to_latest_confirmed():
    c = {"allocated_hours": 2, "may_allocated_hours": 4}
    # july not present -> most recent *_allocated_hours (may) -> 4
    assert cb.resolve_budget(c, "july") == 4


def test_resolve_budget_falls_back_to_base():
    c = {"allocated_hours": 2}
    assert cb.resolve_budget(c, "july") == 2


def test_budget_table_pace_flags():
    customers = [{"tag": "acme", "focus_day": "Monday", "june_allocated_hours": 10}]
    rows = cb.budget_table(customers, {"acme": 2.0}, "june", pct_month_elapsed=0.8)
    r = rows[0]
    assert r["budget_h"] == 10
    assert r["mtd_h"] == 2.0
    assert r["remaining_h"] == 8.0
    assert r["pct_used"] == 0.2
    assert r["pace"] == "under"   # 20% used vs 80% elapsed -> under-pacing


def test_budget_table_pace_on():
    # pct_used (0.5) within ±0.1 of elapsed (0.5) → "on"
    customers = [{"tag": "beta", "focus_day": "Tuesday", "june_allocated_hours": 10}]
    rows = cb.budget_table(customers, {"beta": 5.0}, "june", pct_month_elapsed=0.5)
    assert rows[0]["pace"] == "on"


def test_budget_table_pace_over():
    # pct_used (0.9) well above elapsed (0.5) → "over"
    customers = [{"tag": "gamma", "focus_day": "Wednesday", "june_allocated_hours": 10}]
    rows = cb.budget_table(customers, {"gamma": 9.0}, "june", pct_month_elapsed=0.5)
    assert rows[0]["pace"] == "over"


def test_budget_table_pace_na_zero_budget():
    # budget=0 → pace is "n/a"
    customers = [{"tag": "delta", "focus_day": "Thursday", "allocated_hours": 0}]
    rows = cb.budget_table(customers, {"delta": 0.0}, "june", pct_month_elapsed=0.5)
    assert rows[0]["pace"] == "n/a"


def test_budget_table_multiple_customers():
    customers = [
        {"tag": "first", "focus_day": "Monday", "june_allocated_hours": 10},
        {"tag": "second", "focus_day": "Friday", "june_allocated_hours": 20},
    ]
    rows = cb.budget_table(customers, {"first": 3.0, "second": 10.0}, "june",
                           pct_month_elapsed=0.5)
    assert len(rows) == 2
    assert rows[0]["tag"] == "first"
    assert rows[1]["tag"] == "second"
    # first: 3/10 = 0.3 used vs 0.5 elapsed -> under; second: 10/20 = 0.5 used vs 0.5 -> on
    assert rows[0]["remaining_h"] == 7.0
    assert rows[0]["pace"] == "under"
    assert rows[1]["remaining_h"] == 10.0
    assert rows[1]["pace"] == "on"
