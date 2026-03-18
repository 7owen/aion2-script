import time
from dataclasses import dataclass, field
from enum import Enum

Box = tuple[int, int, int, int]
SIGNAL_WINDOW_SECONDS = 3.0


class CombatSignal(Enum):
    LIWEIJIAN = "liweijian"
    JIAOHUAIZHAN = "jiaohuaizhan"


@dataclass(frozen=True, slots=True)
class PerceptionSnapshot:
    captured_at: float = field(default_factory=time.monotonic)
    health: float | None = None
    mental: float | None = None
    target_box: Box | None = None
    target_distance: int = -1
    resurrection_box: Box | None = None
    active_signals: frozenset[CombatSignal] = field(default_factory=frozenset)
    errors: tuple[str, ...] = ()

    @property
    def has_target(self) -> bool:
        return self.target_box is not None


@dataclass(slots=True)
class SignalWindow:
    expires_at: float = float("-inf")

    def activate(self, duration_seconds: float, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now
        self.expires_at = current_time + duration_seconds

    def is_active(self, now: float | None = None) -> bool:
        current_time = time.monotonic() if now is None else now
        return current_time < self.expires_at

    def clear(self) -> None:
        self.expires_at = float("-inf")


class BotState:
    """机器人运行时状态。融合稳定世界状态和最近一帧感知结果。"""

    def __init__(self, extract_interval_seconds: float):
        self.extract_interval_seconds = extract_interval_seconds
        self.health = 1.0
        self.mental = 1.0
        self.target_box: Box | None = None
        self.target_distance = -1
        self.resurrection_box: Box | None = None
        self.latest_perception = PerceptionSnapshot()
        self.signal_windows = {signal: SignalWindow() for signal in CombatSignal}
        self.next_extract_at = float("inf")
        self.schedule_next_extract()

    @property
    def has_target(self) -> bool:
        return self.target_box is not None

    def apply_perception(self, snapshot: PerceptionSnapshot) -> None:
        self.latest_perception = snapshot

        if snapshot.health is not None:
            self.health = snapshot.health

        if snapshot.mental is not None:
            self.mental = snapshot.mental

        self.target_box = snapshot.target_box
        self.target_distance = snapshot.target_distance if snapshot.has_target else -1
        self.resurrection_box = (
            None if snapshot.has_target else snapshot.resurrection_box
        )

        for signal in snapshot.active_signals:
            self.signal_windows[signal].activate(
                SIGNAL_WINDOW_SECONDS,
                now=snapshot.captured_at,
            )

    def reset_perception(self) -> None:
        self.latest_perception = PerceptionSnapshot()
        self.target_box = None
        self.target_distance = -1
        self.resurrection_box = None

    def need_extract(self) -> bool:
        return time.monotonic() >= self.next_extract_at

    def schedule_next_extract(self) -> None:
        self.next_extract_at = time.monotonic() + self.extract_interval_seconds

    def is_signal_active(self, signal: CombatSignal) -> bool:
        return self.signal_windows[signal].is_active()

    def consume_signal(self, signal: CombatSignal) -> None:
        self.signal_windows[signal].clear()
