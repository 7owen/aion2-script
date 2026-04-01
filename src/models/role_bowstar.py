from __future__ import annotations

import random
import time
from asyncio import sleep
from typing import TYPE_CHECKING

from .role import Role
from .skill_data import (
    BOWSTAR_SKILLS,
    SKILL_BAOZHAJIAN,
    SKILL_BAOZHAQUANTAO,
    SKILL_FENGKUANGJIAN,
    SKILL_JIANSHIFENGBAO,
    SKILL_JUJI,
    SKILL_LIZHUIJIAN,
    SKILL_MIAOZHUNJIAN,
    SKILL_MUBIAOJIAN,
    SKILL_POLIEJIAN,
    SKILL_SUSHE,
    SKILL_TAOSUOJIAN,
    SKILL_TUJITI,
    SKILL_YAZHIJIAN,
)
from .target import Target

if TYPE_CHECKING:
    from factories import SkillFactory


class RoleBowStar(Role):
    def __init__(
        self,
        player_action,
        skill_factory: SkillFactory,
    ) -> None:
        super().__init__(
            player_action=player_action,
            skill_factory=skill_factory,
        )

        create_skill = skill_factory.create_skill
        for skill_metadata in BOWSTAR_SKILLS:
            self.skills[skill_metadata.code] = create_skill(skill_metadata, self)

    def combo_dodge(self, target: Target) -> bool:
        return (
            self.skills[SKILL_TUJITI].use(target)
            or self.skills[SKILL_BAOZHAQUANTAO].use(target)
            or self.player_action.random_dodge(self, 1)
        )

    def search(self) -> None:
        if self.is_casting():
            return

        if self.low_health():
            self.heal_self()
        self.player_action.searching_enemy()

    def start_fight(self, target: Target) -> None:
        if self.is_casting():
            return

        self.skills[SKILL_JUJI].use()
        _ = self.skills[SKILL_JIANSHIFENGBAO].use(target) or self.skills[
            SKILL_TAOSUOJIAN
        ].use(target)

    def end_fight(self, target: Target) -> None:
        pass

    def loop_fight(self, target: Target) -> None:
        if self.is_casting():
            return

        if target.distance > 20:
            self.player_action.random_jump(self, 0.25)

        if 6 > target.distance > 0:
            self.player_action.random_walk(0.25)

        if self.low_health():
            self.heal_self()

        def check_and_dodge(_: Target) -> bool:
            if self.too_close(target):
                return self.combo_dodge(target)
            return False

        skills_to_use = [
            check_and_dodge,
            self.skills[SKILL_LIZHUIJIAN].use,
            self.skills[SKILL_YAZHIJIAN].use,
            self.skills[SKILL_POLIEJIAN].use,
            self.skills[SKILL_MIAOZHUNJIAN].use,
            self.skills[SKILL_MUBIAOJIAN].use,
        ]

        skills_to_use2 = [
            self.skills[SKILL_FENGKUANGJIAN].use,
            self.skills[SKILL_BAOZHAJIAN].use,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skills[SKILL_SUSHE].use)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(target):
                return

        self.skills[SKILL_TAOSUOJIAN].use(target)

    # def buff(self) -> None:
    #     pass
