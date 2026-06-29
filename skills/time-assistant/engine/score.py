"""Config-driven scoring. All thresholds come from a Framework instance —
no module-level scoring constants (that was the single-tenant coupling)."""
from dataclasses import dataclass, field
from typing import List, Optional

from engine.config import Framework


@dataclass
class ClassifiedEvent:
    title: str
    duration_min: int
    label: str            # "HVT" or "LVT"
    category: str
    confidence: float = 1.0
    reason: str = ""
    source: str = "timeular"
    ambiguous: bool = False


@dataclass
class DayScore:
    date: str
    total_minutes: int
    hvt_minutes: int
    lvt_minutes: int
    hvt_ratio: float
    lvt_ratio: float
    breach: bool
    by_category: dict = field(default_factory=dict)
    composite: Optional[int] = None


def score_day(events: List[ClassifiedEvent], framework: Framework,
              planned_events: Optional[List[ClassifiedEvent]] = None,
              date: str = "") -> DayScore:
    total = sum(e.duration_min for e in events)
    hvt = sum(e.duration_min for e in events if e.label == "HVT")
    lvt = sum(e.duration_min for e in events if e.label == "LVT")
    hvt_ratio = hvt / total if total else 0.0
    lvt_ratio = lvt / total if total else 0.0

    by_cat: dict = {}
    for e in events:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.duration_min

    composite = _composite_score(events, planned_events, hvt_ratio, framework)
    return DayScore(
        date=date, total_minutes=total, hvt_minutes=hvt, lvt_minutes=lvt,
        hvt_ratio=round(hvt_ratio, 3), lvt_ratio=round(lvt_ratio, 3),
        breach=lvt_ratio > framework.lvt_cap, by_category=by_cat,
        composite=composite,
    )


def _composite_score(actuals, planned, hvt_ratio, framework: Framework) -> int:
    w = framework.weights
    target = framework.hvt_ratio_target
    floor = 0.5  # ratio at which HVT points hit zero (kept from legacy)

    if hvt_ratio >= target:
        hvt_pts = w["hvt_pts"]
    elif hvt_ratio <= floor:
        hvt_pts = 0
    else:
        hvt_pts = int(w["hvt_pts"] * (hvt_ratio - floor) / (target - floor))

    if not planned:
        adherence_pts = w["adherence_pts"]
    else:
        planned_titles = {p.title.lower().strip() for p in planned}
        actual_titles = {a.title.lower().strip() for a in actuals}
        matched = len(planned_titles & actual_titles)
        adherence = matched / len(planned_titles) if planned_titles else 1.0
        adherence_pts = int(w["adherence_pts"] * adherence)

    if planned:
        planned_titles = {p.title.lower().strip() for p in planned}
        unplanned_lvt = sum(1 for a in actuals
                            if a.label == "LVT"
                            and a.title.lower().strip() not in planned_titles)
    else:
        unplanned_lvt = sum(1 for a in actuals if a.label == "LVT")

    full_max = w["frag_full_max"]
    zero_min = w["frag_zero_min"]
    if unplanned_lvt <= full_max:
        frag_pts = w["frag_pts"]
    elif unplanned_lvt >= zero_min:
        frag_pts = 0
    else:
        span = zero_min - full_max
        frag_pts = int(w["frag_pts"] * (zero_min - unplanned_lvt) / span)

    return min(100, hvt_pts + adherence_pts + frag_pts)


def week_to_date_ratio(daily_scores: List[dict]) -> dict:
    total = sum(d.get("total_minutes", 0) for d in daily_scores)
    hvt = sum(d.get("hvt_minutes", 0) for d in daily_scores)
    lvt = sum(d.get("lvt_minutes", 0) for d in daily_scores)
    breach_days = sum(1 for d in daily_scores if d.get("breach"))
    return {
        "total_minutes": total, "hvt_minutes": hvt, "lvt_minutes": lvt,
        "hvt_ratio": round(hvt / total, 3) if total else 0.0,
        "lvt_ratio": round(lvt / total, 3) if total else 0.0,
        "breach_days": breach_days, "days_counted": len(daily_scores),
    }
