from __future__ import annotations

import time

from .buff import Buff
from .skill import Skill


class Creature:
    """所有生物的基类，包含生命值、魔法值、Buff/Skill 状态"""

    def __init__(self):
        self.health: float = 1.0
        self.mental: float = 1.0
        self.buffs: dict[str, Buff] = {}
        self.skills: dict[str, Skill] = {}

    def is_active_buff(self, buff_code: str) -> bool:
        return buff_code in self.buffs and self.buffs[buff_code].is_activated()

    def consume_buff(self, buff_code: str) -> None:
        if buff_code in self.buffs:
            self.buffs[buff_code].clear()

    def active_buff(self, buff_code: str, now: float) -> None:
        """添加或更新一个 Buff"""
        if buff_code in self.buffs:
            self.buffs[buff_code].activate(now)

    def clear_buffs(self) -> None:
        for buff in self.buffs.values():
            buff.clear()

    def get_buff_info(self) -> str:
        active_buffs = []
        now = time.monotonic()
        for buff in self.buffs.values():
            if buff.is_activated():
                remaining = buff.expires_at - now
                active_buffs.append(f"{buff.name}({remaining:.1f}s)")
        return " | ".join(active_buffs) if active_buffs else "无"
