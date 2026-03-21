import time
from dataclasses import dataclass, field

from bot_config import config
from models.role import Role
from models.target import Target

Box = tuple[int, int, int, int]
BUFF_WINDOW_SECONDS = 1.0


@dataclass(frozen=True, slots=True)
class PerceptionSnapshot:
    captured_at: float = field(default_factory=time.monotonic)
    health: float | None = None
    mental: float | None = None
    target_box: Box | None = None
    target_distance: int = -1
    resurrection_box: Box | None = None
    active_buff_codes: frozenset[str] = field(default_factory=frozenset)
    errors: tuple[str, ...] = ()

    @property
    def has_target(self) -> bool:
        return self.target_box is not None


class BotState:
    """机器人运行时状态。融合稳定世界状态和最近一帧感知结果。"""

    def __init__(self, role: Role):
        self.role = role
        self.target: Target = Target()
        self.last_target_seen_at = float("-inf")
        self.resurrection_btn: Box | None = None
        self.latest_perception = PerceptionSnapshot()
        self.next_extract_at = float("inf")
        self.schedule_next_extract()

    @property
    def has_target(self) -> bool:
        return self.target.has_target

    def apply_perception(self, snapshot: PerceptionSnapshot) -> None:
        self.latest_perception = snapshot

        if snapshot.health is not None:
            self.role.health = snapshot.health

        if snapshot.mental is not None:
            self.role.mental = snapshot.mental

        if snapshot.has_target:
            self.last_target_seen_at = snapshot.captured_at
            self.target.has_target = snapshot.has_target
            if snapshot.target_distance > 0:
                self.target.distance = snapshot.target_distance

            for buff_code in snapshot.active_buff_codes:
                if self.role.valid_buff(buff_code) and not self.role.buff_activated(
                    buff_code
                ):
                    self.role.active_buff(buff_code, snapshot.captured_at)
                elif self.target.valid_buff(
                    buff_code
                ) and not self.target.buff_activated(buff_code):
                    self.target.active_buff(buff_code, snapshot.captured_at)
        elif snapshot.captured_at - self.last_target_seen_at >= BUFF_WINDOW_SECONDS:
            self.target.clear()
        else:
            self.target.has_target = True

        self.resurrection_btn = snapshot.resurrection_box

    def reset_perception(self) -> None:
        self.latest_perception = PerceptionSnapshot()
        self.last_target_seen_at = float("-inf")
        self.target.clear()
        self.resurrection_btn = None

    def need_extract(self) -> bool:
        return time.monotonic() >= self.next_extract_at

    def schedule_next_extract(self) -> None:
        self.next_extract_at = time.monotonic() + config.role.extract_interval_seconds
