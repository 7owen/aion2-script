from __future__ import annotations

import datetime
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

        if target:
            if target.distance < self.metadata.min_range:
                return False
            if (
                self.metadata.max_range is not None
                and target.distance > self.metadata.max_range
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

        print(f"[{used_at:.3f}] 释放技能: {self.name} ({self.code})")
        self.last_used_at = used_at
        self.for_role.action_end_at = used_at + self.metadata.time_consumption

        for i in range(self.metadata.press_count):
            self._press_once()
            if i < self.metadata.press_count - 1:
                time.sleep(self.metadata.press_interval)

        # for bc in self.metadata.require_buff_codes:
        #     if self.for_role.is_active_buff(bc):
        #         print(f"[{used_at:.3f}] 消费 Buff: {bc} (来源: 自身)")
        #     self.for_role.consume_buff(bc)
        #     if target:
        #         if target.is_active_buff(bc):
        #             print(f"[{used_at:.3f}] 消费 Buff: {bc} (来源: 目标)")
        #         target.consume_buff(bc)

        # 4. 生成 Buff
        if self.metadata.generate_buff_codes:
            for bc in self.metadata.generate_buff_codes:
                self.for_role.active_buff(bc, self.for_role.action_end_at)
                if target is not None:
                    target.active_buff(bc, self.for_role.action_end_at)

        return True

    def _press_once(self) -> None:
        """底层封装的单次释放技能逻辑，可根据配置执行两次按键防吞"""
        # 第一次按下
        if self.metadata.press_holdon is not None:
            self.kmDriver.key_press(self.metadata.key, self.metadata.press_holdon)
        else:
            self.kmDriver.key_press(self.metadata.key)

        # 如果启用了防吞键机制，则执行第二次按下
        if self.metadata.anti_swallow:
            # 延迟 0.1 秒
            time.sleep(0.1)

            # 第二次按下，防动画卡键或丢包
            if self.metadata.press_holdon is not None:
                self.kmDriver.key_press(self.metadata.key, self.metadata.press_holdon)
            else:
                self.kmDriver.key_press(self.metadata.key)
