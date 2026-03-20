from __future__ import annotations

import random
from abc import ABC, abstractmethod

import kmbox_net

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
        skill_factory: SkillFactory,
        state: BotState,
    ) -> None:
        self.config = config
        self.state = state
        self.player_action = player_action

        create_skill = skill_factory.create_skill

        self.skill_f1 = create_skill(
            "回血",
            kmbox_net.KEY_F1,
            cooldown=15,
            impact_time=2,
        )

        self.skill_jump = create_skill("跳跃", kmbox_net.KEY_SPACEBAR)

        self.skill_shift = create_skill(
            "紧急回避",
            kmbox_net.KEY_LEFTSHIFT,
            cooldown=1,
            impact_time=1,
        )

    def jump(self) -> bool:
        return self.skill_jump.use(self.state.target_distance)

    def dodge(self) -> bool:
        return self.skill_shift.use(self.state.target_distance)

    def heal_self(self) -> bool:
        return self.skill_f1.use(self.state.target_distance)

    @abstractmethod
    def search(self) -> None:
        pass

    @abstractmethod
    def fight(self) -> None:
        pass

    def buff(self) -> None:
        pass

    def low_health(self) -> bool:
        return (
            self.state.health > 0
            and self.state.health < self.config.low_health_threshold
        )

    def too_close(self) -> bool:
        return (
            self.state.target_distance > 0
            and self.state.target_distance <= self.config.close_distance_threshold
        )

    def get_skill_cd_info(self) -> str:
        cd_parts = []
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, Skill):
                if attr_value.is_ready():
                    cd_parts.append(f"{attr_value.name}")
                else:
                    remaining = attr_value.get_remaining_cd()
                    cd_parts.append(f"{attr_value.name}({remaining:.1f}s)")

        return " | ".join(cd_parts)
