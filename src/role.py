from __future__ import annotations

import random
from abc import ABC, abstractmethod

from bot_config import RoleConfig
from console import console as console
from game_context import GameContext
from km_driver import KmboxDriver
from player_controller import PlayerController
from skill import Skill


class Role(ABC):
    def __init__(
        self,
        km_driver: KmboxDriver,
        config: RoleConfig,
        player_ctrl: PlayerController,
        context: GameContext,
    ) -> None:
        self.config = config
        self.context = context
        self.player_ctrl = player_ctrl

        self.kmDriver = km_driver

    @abstractmethod
    def search(self):
        pass

    @abstractmethod
    def fight(self):
        pass

    @abstractmethod
    def buff(self):
        pass

    def is_low_health(self):
        return (
            self.context.health > 0
            and self.context.health < self.config.low_health_threshold
        )

    def check_low_health(self):
        if self.is_low_health():
            # console.set_note_msg("生命值低")
            return True
        return False

    def is_close(self):
        return (
            self.context.target_distance > 0
            and self.context.target_distance <= self.config.close_distance_threshold
        )

    def check_is_close(self):
        if self.is_close():
            console.set_note_msg("距离目标太近")
            return True if random.randint(0, 1) == 1 else False
        return False

    def get_skill_cd_info(self):
        cd_parts = []
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, Skill):
                is_off_cd = attr_value.is_off_cooldown()
                if is_off_cd:
                    cd_parts.append(f"{attr_value.name}")
                else:
                    remaining = attr_value.get_remaining_cd()
                    cd_parts.append(f"{attr_value.name}({remaining:.1f}s)")

        return " | ".join(cd_parts)
