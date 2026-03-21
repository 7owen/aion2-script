from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .buff import Buff
from .role import Role
from .skill_data import (
    FENNUBODONG,
    FENSUIBODONG,
    JIAOHUAIZHAN,
    JINUBAOZHA,
    KONGZHONGJIEFU,
    POMIEMENGJI,
    QIANGXIYIJI,
    ROULINJIAN,
    RUILIYIJI,
    SWORDSTAR_BUFFS,
    SWORDSTAR_SKILLS,
    TIAOYUEGONGJI,
    TUJINYIJI,
    XIAPANJI,
    ZHANDUANMENGJI,
)
from .target import Target

if TYPE_CHECKING:
    from factories import SkillFactory


class RoleSwordStar(Role):
    def __init__(self, player_action, skill_factory: SkillFactory) -> None:
        super().__init__(
            player_action=player_action,
            skill_factory=skill_factory,
        )

        for buff_code in SWORDSTAR_BUFFS:
            self.buffs[buff_code] = Buff(SWORDSTAR_BUFFS[buff_code])

        create_skill = skill_factory.create_skill
        for skill_code in SWORDSTAR_SKILLS:
            self.skills[skill_code] = create_skill(SWORDSTAR_SKILLS[skill_code], self)

    def search(self) -> None:
        if self.low_health():
            self.heal_self()
        self.skills[RUILIYIJI].use()

    def first_fight(self, target: Target) -> None:
        _ = (
            self.skills[TIAOYUEGONGJI].use(target)
            or self.skills[POMIEMENGJI].use(target)
            or self.skills[QIANGXIYIJI].use(target)
        )

    def loop_fight(self, target: Target) -> None:
        if target.distance > 20:
            self.player_action.random_jump(self, 0.25)

        if 6 > target.distance > 0:
            self.player_action.random_walk(0.25)

        if self.low_health():
            self.heal_self()

        def com_skill_q2(target: Target) -> bool:
            if self.skills[TUJINYIJI].can_use(target):
                if self.player_action.random_dodge(self, 1):
                    return self.skills[TUJINYIJI].use(target)
            return False

        skills_to_use = [
            self.skills[KONGZHONGJIEFU].use,
            self.skills[XIAPANJI].use,
            self.skills[JIAOHUAIZHAN].use,
            self.skills[FENSUIBODONG].use,
        ]
        skills_to_use2 = [
            self.skills[QIANGXIYIJI].use,
            self.skills[FENNUBODONG].use,
            self.skills[JINUBAOZHA].use,
            self.skills[ROULINJIAN].use,
            com_skill_q2,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skills[ZHANDUANMENGJI].use)

        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(target):
                return

        self.skills[TIAOYUEGONGJI].use(target)
