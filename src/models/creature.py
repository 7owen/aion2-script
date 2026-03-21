from __future__ import annotations

from .buff import Buff
from .skill import Skill


class Creature:
    """所有生物的基类，包含生命值、魔法值、Buff/Skill 状态"""

    def __init__(self):
        self.health: float = 1.0
        self.mental: float = 1.0
        self.buffs: dict[str, Buff] = {}
        self.skills: dict[str, Skill] = {}

    def valid_buff(self, buff_code: str) -> bool:
        return buff_code in self.buffs

    def buff_activated(self, buff_code: str) -> bool:
        return self.valid_buff(buff_code) and self.buffs[buff_code].is_activated()

    def consume_buff(self, buff_code: str) -> None:
        if buff_code in self.buffs:
            self.buffs[buff_code].clear()

    def active_buff(self, buff_code: str, now: float) -> None:
        """添加或更新一个 Buff"""
        if buff_code in self.buffs:
            self.buffs[buff_code].activate(now)
