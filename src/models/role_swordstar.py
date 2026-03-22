from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .role import Role
from .skill_data import (
    SKILL_FENNUBODONG,
    SKILL_FENSUIBODONG,
    SKILL_JIAOHUAIZHAN,
    SKILL_JINUBAOZHA,
    SKILL_KONGZHONGJIEFU,
    SKILL_POMIEMENGJI,
    SKILL_QIANGXIYIJI,
    SKILL_ROULINJIAN,
    SKILL_RUILIYIJI,
    SKILL_TIAOYUEGONGJI,
    SKILL_TUJINYIJI,
    SKILL_XIAPANJI,
    SKILL_ZHANDUANMENGJI,
    SWORDSTAR_SKILLS,
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

        create_skill = skill_factory.create_skill
        for skill_metadata in SWORDSTAR_SKILLS:
            self.skills[skill_metadata.code] = create_skill(skill_metadata, self)

    def search(self) -> None:
        if self.low_health():
            self.heal_self()
        self.player_action.searching_enemy()

    def first_fight(self, target: Target) -> None:
        # self.skills[SKILL_RUILIYIJI].use(target)
        _ = (
            self.skills[SKILL_QIANGXIYIJI].use(target)
            or self.skills[SKILL_POMIEMENGJI].use(target)
            or self.skills[SKILL_TIAOYUEGONGJI].use(target)
        )

    def loop_fight(self, target: Target) -> None:
        if target.distance > 20:
            self.player_action.random_jump(self, 0.25)

        if 5 > target.distance > 0:
            self.player_action.random_walk(0.25)

        if self.low_health():
            self.heal_self()

        def com_skill_q2(target: Target) -> bool:
            if self.skills[SKILL_TUJINYIJI].can_use(target):
                if self.player_action.random_dodge(self, 1):
                    return self.skills[SKILL_TUJINYIJI].use(target)
            return False

        skills_to_use = [
            self.skills[SKILL_KONGZHONGJIEFU].use,
            self.skills[SKILL_XIAPANJI].use,
            self.skills[SKILL_JIAOHUAIZHAN].use,
            self.skills[SKILL_FENSUIBODONG].use,
        ]
        skills_to_use2 = [
            self.skills[SKILL_QIANGXIYIJI].use,
            self.skills[SKILL_FENNUBODONG].use,
            self.skills[SKILL_JINUBAOZHA].use,
            self.skills[SKILL_ROULINJIAN].use,
            com_skill_q2,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skills[SKILL_ZHANDUANMENGJI].use)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(target):
                return

        self.skills[SKILL_TIAOYUEGONGJI].use(target)
