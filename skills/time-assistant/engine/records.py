"""Normalized record types every integration adapter emits.

Adapters translate their tool-specific JSON into these shapes so the engine
never needs to know which source produced a record.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime


def _iso(s: str) -> datetime:
    # Accept trailing 'Z' and millisecond precision.
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def _duration_min(start: str, end: str) -> int:
    if not start or not end:
        return 0
    delta = _iso(end) - _iso(start)
    return int(delta.total_seconds() // 60)


@dataclass(eq=True)
class TimeRecord:
    start: str
    end: str
    activity: str
    tags: list = field(default_factory=list)
    note: str = ""
    source: str = ""
    duration_min: int = 0

    def __post_init__(self):
        if not self.duration_min:
            self.duration_min = _duration_min(self.start, self.end)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TimeRecord":
        return cls(
            start=d.get("start", ""), end=d.get("end", ""),
            activity=d.get("activity", ""), tags=list(d.get("tags", [])),
            note=d.get("note", ""), source=d.get("source", ""),
            duration_min=d.get("duration_min", 0),
        )


@dataclass(eq=True)
class BiometricRecord:
    date: str
    metric: str
    value: float
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BiometricRecord":
        return cls(date=d["date"], metric=d["metric"],
                   value=float(d["value"]), source=d.get("source", ""))


@dataclass(eq=True)
class ActivityRecord:
    date: str
    type: str
    duration_min: int
    intensity: float = 0.0
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ActivityRecord":
        return cls(date=d["date"], type=d["type"],
                   duration_min=int(d["duration_min"]),
                   intensity=float(d.get("intensity", 0.0)),
                   source=d.get("source", ""))
