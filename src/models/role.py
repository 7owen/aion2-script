from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bot_config import config
from player_actions import PlayerActions

from .creature import Creature
from .skill_data import COMMON_SKILLS, HUIXUE, JINJIHUIBI, TIAOYUE
from .target import Target

if TYPE_CHECKING:
    from factories import SkillFactory


class Role(Creature, ABC):
    def __init__(
        self,
        player_action: PlayerActions,
        skill_factory: SkillFactory,
    ) -> None:
        super().__init__()
        self.config = config.role
        self.player_action = player_action

        create_skill = skill_factory.create_skill
        for skill_code in COMMON_SKILLS:
            self.skills[skill_code] = create_skill(COMMON_SKILLS[skill_code], self)

    def jump(self) -> bool:
        return self.skills[TIAOYUE].use()

    def dodge(self) -> bool:
        return self.skills[JINJIHUIBI].use()

    def heal_self(self) -> bool:
        return self.skills[HUIXUE].use()

    @abstractmethod
    def search(self) -> None:
        pass

    @abstractmethod
    def first_fight(self, target: Target) -> None:
        pass

    @abstractmethod
    def loop_fight(self, target: Target) -> None:
        pass

    def buff(self) -> None:
        pass

    def low_health(self) -> bool:
        return self.health > 0 and self.health < config.role.low_health_threshold

    def too_close(self, target: Target) -> bool:
        return (
            target.distance > 0
            and target.distance <= config.role.close_distance_threshold
        )

    def get_skill_cd_info(self) -> str:
        cd_parts = []
        for skill in self.skills.values():
            if skill.ready():
                cd_parts.append(f"{skill.name}")
            else:
                remaining = skill.get_remaining_cd()
                cd_parts.append(f"{skill.name}({remaining:.1f}s)")

        return " | ".join(cd_parts)
