from engine.config import DEFAULT_FRAMEWORK
from engine.score import ClassifiedEvent, score_day, week_to_date_ratio

F = DEFAULT_FRAMEWORK


def ev(label, cat, mins, title="x"):
    return ClassifiedEvent(title=title, duration_min=mins, label=label, category=cat)


def test_hvt_ratio_and_breach():
    events = [ev("HVT", "strategic", 240), ev("LVT", "email", 60)]
    ds = score_day(events, F, date="2026-06-01")
    assert ds.total_minutes == 300
    assert ds.hvt_ratio == 0.8
    assert ds.lvt_ratio == 0.2
    assert ds.breach is False


def test_breach_when_lvt_over_cap():
    events = [ev("HVT", "strategic", 100), ev("LVT", "email", 100)]
    ds = score_day(events, F)
    assert ds.breach is True  # lvt_ratio 0.5 > 0.20


def test_composite_full_when_target_met_no_plan():
    events = [ev("HVT", "strategic", 480)]
    ds = score_day(events, F)
    # 60 (hvt) + 20 (no plan = neutral) + 20 (0 unplanned LVT) = 100
    assert ds.composite == 100


def test_composite_hvt_partial_scaling():
    # hvt_ratio = 0.65 -> between 0.5 and 0.8 -> 60*(.15/.30)=30
    events = [ev("HVT", "strategic", 130), ev("LVT", "email", 70)]
    ds = score_day(events, F)
    # frag: 1 unplanned LVT <=2 -> 20 ; no plan -> 20 ; hvt 30
    assert ds.composite == 70


def test_custom_framework_changes_target():
    from dataclasses import replace
    f2 = replace(F, hvt_ratio_target=0.60)
    events = [ev("HVT", "strategic", 120), ev("LVT", "email", 80)]  # ratio 0.6
    # Lowered target is met -> full hvt pts -> 60 + 20 (no plan) + 20 (1 unplanned LVT) = 100
    assert score_day(events, f2).composite == 100
    # Same events under the default target (0.80) are NOT full -> strictly lower.
    assert score_day(events, F).composite < 100


def test_score_day_with_plan_adherence_and_unplanned_lvt():
    planned = [ev("HVT", "strategic", 240, "deep work"),
               ev("LVT", "email", 60, "inbox")]
    actuals = [ev("HVT", "strategic", 240, "deep work"),     # matches plan
               ev("LVT", "email", 60, "surprise call")]      # unplanned LVT
    ds = score_day(actuals, F, planned_events=planned, date="2026-06-01")
    # hvt_ratio 0.8 -> hvt_pts 60; adherence matched 1/2 -> 10; 1 unplanned LVT (<=2) -> 20
    assert ds.composite == 90


def test_week_to_date_ratio():
    rows = [
        {"total_minutes": 300, "hvt_minutes": 240, "lvt_minutes": 60, "breach": False},
        {"total_minutes": 200, "hvt_minutes": 100, "lvt_minutes": 100, "breach": True},
    ]
    wtd = week_to_date_ratio(rows)
    assert wtd["total_minutes"] == 500
    assert wtd["hvt_ratio"] == 0.68
    assert wtd["breach_days"] == 1
