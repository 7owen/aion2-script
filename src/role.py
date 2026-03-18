from __future__ import annotations

import random
from abc import ABC, abstractmethod

from bot_config import RoleConfig
from console import console as console
from game_context import BotState
from player_actions import PlayerActions
from skill import Skill
from skill_factory import SkillFactory


class Role(ABC):
    def __init__(
        self,
        config: RoleConfig,
        player_action: PlayerActions,
        state: BotState,
    ) -> None:
        self.config = config
        self.state = state
        self.player_action = player_action

    @abstractmethod
    def search(self) -> None:
        pass

    @abstractmethod
    def fight(self) -> None:
        pass

    @abstractmethod
    def buff(self) -> None:
        pass

    @abstractmethod
    def dodge(self) -> bool:
        pass

    def is_low_health(self) -> bool:
        return (
            self.state.health > 0
            and self.state.health < self.config.low_health_threshold
        )

    def check_low_health(self) -> bool:
        return self.is_low_health()

    def heal_self(self) -> bool:
        console.set_note_msg(f"恢复生命, 剩余{self.state.health * 100:.2f}%")
        return self.player_action.heal(self.state.target_distance)

    def is_close(self) -> bool:
        return (
            self.state.target_distance > 0
            and self.state.target_distance <= self.config.close_distance_threshold
        )

    def check_is_close(self) -> bool:
        if self.is_close():
            console.set_note_msg("距离目标太近")
            return random.randint(0, 1) == 1
        return False

    def get_skill_cd_info(self) -> str:
        cd_parts = []
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, Skill):
                if attr_value.is_off_cooldown():
                    cd_parts.append(f"{attr_value.name}")
                else:
                    remaining = attr_value.get_remaining_cd()
                    cd_parts.append(f"{attr_value.name}({remaining:.1f}s)")

        return " | ".join(cd_parts)
