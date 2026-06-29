"""Optional consulting module: per-client monthly budget tracker.
Enabled only when the tenant config lists 'client_budget' in modules."""
from engine.config import TenantConfig

_MONTHS = ["january", "february", "march", "april", "may", "june",
           "july", "august", "september", "october", "november", "december"]


def is_enabled(config: TenantConfig) -> bool:
    return "client_budget" in (config.modules or [])


def resolve_budget(customer: dict, month_key: str) -> float:
    key = f"{month_key}_allocated_hours"
    if key in customer:
        return float(customer[key])
    # Most recent *_allocated_hours by calendar order, else base.
    present = [(m, customer[f"{m}_allocated_hours"]) for m in _MONTHS
               if f"{m}_allocated_hours" in customer]
    if present:
        present.sort(key=lambda mv: _MONTHS.index(mv[0]))
        return float(present[-1][1])
    return float(customer.get("allocated_hours", 0))


def budget_table(customers: list, mtd_by_tag: dict, month_key: str,
                 pct_month_elapsed: float) -> list:
    rows = []
    for c in customers:
        tag = c.get("tag", "")
        budget = resolve_budget(c, month_key)
        mtd = float(mtd_by_tag.get(tag, 0.0))
        remaining = round(budget - mtd, 2)
        pct_used = round(mtd / budget, 2) if budget else 0.0
        if budget == 0:
            pace = "n/a"
        elif pct_used + 0.1 < pct_month_elapsed:
            pace = "under"
        elif pct_used > pct_month_elapsed + 0.1:
            pace = "over"
        else:
            pace = "on"
        rows.append({
            "tag": tag, "focus_day": c.get("focus_day", ""),
            "budget_h": budget, "mtd_h": mtd, "remaining_h": remaining,
            "pct_used": pct_used, "pace": pace,
        })
    return rows
