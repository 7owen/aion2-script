from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .buff import Buff
from .role import Role
from .skill_data import (
    BAOZHAJIAN,
    BAOZHAQUANTAO,
    BOWSTAR_BUFFS,
    BOWSTAR_SKILLS,
    FENGKUANGJIAN,
    JIANSHIFENGBAO,
    JUJI,
    LIZHUIJIAN,
    MIAOZHUNJIAN,
    MUBIAOJIAN,
    POLIEJIAN,
    SUSHE,
    TAOSUOJIAN,
    TUJITI,
    YAZHIJIAN,
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

        for buff_code in BOWSTAR_BUFFS:
            self.buffs[buff_code] = Buff(BOWSTAR_BUFFS[buff_code])

        create_skill = skill_factory.create_skill
        for skill_code in BOWSTAR_SKILLS:
            self.skills[skill_code] = create_skill(BOWSTAR_SKILLS[skill_code], self)

    def combo_dodge(self, target: Target) -> bool:
        return (
            self.skills[TUJITI].use(target)
            or (
                self.skills[BAOZHAQUANTAO].use(target)
                and self.player_action.random_dodge(self, 1)
            )
            or self.player_action.random_dodge(self, 1)
        )

    def search(self) -> None:
        if self.low_health():
            self.heal_self()
        self.skills[JUJI].use()

    def first_fight(self, target: Target) -> None:
        _ = self.skills[JIANSHIFENGBAO].use(target) or self.skills[TAOSUOJIAN].use(
            target
        )

    def loop_fight(self, target: Target) -> None:
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
            self.skills[POLIEJIAN].use,
            self.skills[LIZHUIJIAN].use,
            self.skills[YAZHIJIAN].use,
            self.skills[MIAOZHUNJIAN].use,
            self.skills[MUBIAOJIAN].use,
        ]

        skills_to_use2 = [
            self.skills[FENGKUANGJIAN].use,
            self.skills[BAOZHAJIAN].use,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skills[SUSHE].use)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(target):
                return

        self.skills[TAOSUOJIAN].use(target)

    # def buff(self) -> None:
    #     pass
