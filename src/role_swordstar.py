import random

import kmbox_net

from bot_config import RoleConfig
from game_context import BotState, CombatSignal
from role import Role
from skill_factory import SkillFactory


class RoleSwordStar(Role):
    def __init__(
        self,
        role_config: RoleConfig,
        player_action,
        skill_factory: SkillFactory,
        state: BotState,
    ) -> None:
        super().__init__(
            config=role_config,
            player_action=player_action,
            skill_factory=skill_factory,
            state=state,
        )
        create_skill = skill_factory.create_skill
        self.skill_1 = create_skill(
            "跳跃攻击",
            kmbox_net.KEY_1,
            cooldown=15 + 1,
        )

        self.skill_2 = create_skill(
            "蹂躏剑",
            kmbox_net.KEY_2,
            cooldown=20 + 1,
            max_range=4,
            time_consumption=1.5,
            impact_time=3,
        )

        self.skill_3 = create_skill(
            "粉碎波动",
            kmbox_net.KEY_3,
            cooldown=20 + 1,
            max_range=4,
            time_consumption=2,
            press_count=2,
        )

        self.skill_4 = create_skill(
            "破灭猛击",
            kmbox_net.KEY_4,
            cooldown=30,
        )

        self.skill_5 = create_skill(
            "愤怒波动",
            kmbox_net.KEY_5,
            cooldown=60 + 1,
            max_range=4,
            impact_time=3,
            time_consumption=1,
        )
        self.skill_6 = create_skill(
            "强袭一击",
            kmbox_net.KEY_6,
            cooldown=120 + 1,
            impact_time=3,
        )

        self.skill_7 = create_skill(
            "激怒爆炸",
            kmbox_net.KEY_7,
            cooldown=45 + 1,
            max_range=4,
            time_consumption=1,
            impact_time=10,
        )

        self.skill_e1 = create_skill(
            "脚踝斩",
            kmbox_net.KEY_E,
            cooldown=10 + 1,
            max_range=4,
            impact_time=3,
        )

        self.skill_r = create_skill(
            "锐利一击",
            kmbox_net.KEY_R,
        )

        self.skill_t = create_skill(
            "斩断猛击",
            kmbox_net.KEY_T,
            max_range=4,
        )

        self.skill_q2 = create_skill(
            "突进一击",
            kmbox_net.KEY_Q,
            cooldown=20 + 1,
            max_range=4,
            impact_time=3,
        )

        self.skill_q1 = create_skill(
            "空中结缚",
            kmbox_net.KEY_Q,
            cooldown=45 + 1,
            max_range=4,
            impact_time=3,
        )

        self.skill_e2 = create_skill(
            "下盘击",
            kmbox_net.KEY_E,
            cooldown=5 + 1,
            max_range=4,
            time_consumption=1.5,
            press_count=2,
        )

        self.skill_q1.add_precondition_skills(
            self.skill_2,
            self.skill_q2,
            self.skill_6,
            self.skill_5,
            self.skill_7,
        )

        self.skill_e2.add_precondition_skills(
            self.skill_2,
            self.skill_q2,
            self.skill_6,
            self.skill_5,
            self.skill_7,
        )

        self.skill_2.add_mutual_exclusion_skills(
            self.skill_q1, self.skill_q2, self.skill_7, self.skill_e1, self.skill_6
        )

        self.skill_7.add_mutual_exclusion_skills(
            self.skill_q2, self.skill_2, self.skill_6
        )

        self.skill_q2.add_mutual_exclusion_skills(self.skill_2, self.skill_7)

        self.skill_6.add_mutual_exclusion_skills(
            self.skill_q1, self.skill_q2, self.skill_7, self.skill_e1, self.skill_2
        )

    def search(self) -> None:
        if self.low_health():
            self.heal_self()

        _ = (
            self.skill_1.use(self.state.target_distance)
            or self.skill_4.use(self.state.target_distance)
            or self.skill_6.use(self.state.target_distance)
            or self.skill_r.use(self.state.target_distance)
        )

    def fight(self) -> None:
        if self.state.target_distance > 20:
            self.player_action.random_jump(self, 0.25)

        if 6 > self.state.target_distance > 0:
            self.player_action.random_walk(0.25)

        def check_and_heal(_: int) -> bool:
            if self.low_health():
                return self.heal_self()
            return False

        def com_skill_q2(target_distance: int) -> bool:
            if self.skill_q2.can_use(target_distance):
                self.player_action.random_dodge(self, 1)
                return self.skill_q2.use(target_distance)
            return False

        def com_skill_e1(target_distance: int) -> bool:
            if self.skill_e1.can_use(target_distance) and self.state.is_signal_active(
                CombatSignal.JIAOHUAIZHAN
            ):
                used = self.skill_e1.use(target_distance)
                if used:
                    self.state.consume_signal(CombatSignal.JIAOHUAIZHAN)
                return used
            return False

        skills_to_use = [
            check_and_heal,
            self.skill_q1.use,
            self.skill_e2.use,
            com_skill_e1,
        ]
        skills_to_use2 = [
            self.skill_3.use,
            self.skill_6.use,
            self.skill_5.use,
            self.skill_7.use,
            self.skill_2.use,
            com_skill_q2,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skill_t.use)

        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(self.state.target_distance):
                return

        self.skill_1.use(self.state.target_distance)

    # def buff(self) -> None:
    #     pass
