from __future__ import annotations

import time
from typing import TYPE_CHECKING

from km_driver import KmboxDriver

from .metadata import SkillMetadata

if TYPE_CHECKING:
    from .role import Role
    from .target import Target


class Skill:
    def __init__(self, metadata: SkillMetadata, km_driver: KmboxDriver, for_role: Role):
        self.metadata = metadata
        self.kmDriver = km_driver
        self.last_used_at = 0.0
        self.for_role = for_role

    @property
    def code(self) -> str:
        return self.metadata.code

    @property
    def name(self) -> str:
        return self.metadata.name

    def __hash__(self) -> int:
        return hash(self.metadata.code)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Skill):
            return self.metadata.code == other.metadata.code
        return False

    def ready(self) -> bool:
        return self.get_remaining_cd() <= 0

    def get_remaining_cd(self) -> float:
        elapsed = time.monotonic() - self.last_used_at
        return max(0, self.metadata.cooldown - elapsed)

    def can_use(self, target: Target | None = None) -> bool:
        # if self.for_role.is_casting():
        #     return False

        if not self.ready():
            return False

        if (
            target
            and self.metadata.max_range is not None
            and not (0 <= target.distance <= self.metadata.max_range)
        ):
            return False

        if not self.metadata.require_buff_codes:
            return True

        for bc in self.metadata.require_buff_codes:
            # 检查自己或目标是否有该 Buff
            if self.for_role.is_active_buff(bc) or (
                target and target.is_active_buff(bc)
            ):
                return True

        return False

    def use(self, target: Target | None = None) -> bool:
        if not self.can_use(target):
            return False

        used_at = time.monotonic()
        self.last_used_at = used_at
        self.for_role.action_end_at = used_at + self.metadata.time_consumption

        for i in range(self.metadata.press_count):
            self._press_once()
            if i < self.metadata.press_count - 1:
                time.sleep(self.metadata.press_interval)

        # for bc in self.metadata.require_buff_codes:
        #     self.for_role.consume_buff(bc)
        #     if target:
        #         target.consume_buff(bc)

        # 4. 生成 Buff
        if self.metadata.generate_buff_codes:
            for bc in self.metadata.generate_buff_codes:
                now = time.monotonic()
                self.for_role.active_buff(bc, now)
                if target is not None:
                    target.active_buff(bc, now)

        return True

    def _press_once(self) -> None:
        if self.metadata.press_holdon is not None:
            self.kmDriver.key_press(self.metadata.key, self.metadata.press_holdon)
        else:
            self.kmDriver.key_press(self.metadata.key)
