import random

import kmbox_net

from bot_config import RoleConfig
from game_context import BotState, CombatSignal
from role import Role
from skill_factory import SkillFactory


class RoleBowStar(Role):
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
            "套索箭",
            kmbox_net.KEY_1,
            cooldown=15 + 1,
            impact_time=5,
        )
        self.skill_2 = create_skill(
            "疯狂箭",
            kmbox_net.KEY_2,
            cooldown=20 + 1,
            max_range=20,
            press_holdon=0.5,
        )
        self.skill_3 = create_skill(
            "爆炸圈套",
            kmbox_net.KEY_3,
            cooldown=20 + 1,
            max_range=20,
            impact_time=3,
        )
        self.skill_5 = create_skill(
            "箭失风暴",
            kmbox_net.KEY_5,
            cooldown=60 + 1,
            impact_time=10,
        )
        self.skill_6 = create_skill(
            "突击踢",
            kmbox_net.KEY_6,
            cooldown=30,
            max_range=5,
        )
        self.skill_7 = create_skill(
            "白什么灌能",
            kmbox_net.KEY_7,
            cooldown=60 + 1,
        )
        self.skill_8 = create_skill(
            "爆炸箭",
            kmbox_net.KEY_8,
            cooldown=45 + 1,
            max_range=20,
        )

        self.skill_q2 = create_skill(
            "利锥箭",
            kmbox_net.KEY_Q,
            cooldown=5,
            max_range=20,
        )
        self.skill_e1 = create_skill(
            "目标箭",
            kmbox_net.KEY_E,
            cooldown=10 + 1,
            max_range=20,
            impact_time=10,
        )
        self.skill_e2 = create_skill(
            "压制箭",
            kmbox_net.KEY_E,
            cooldown=20 + 1,
            max_range=20,
            impact_time=4,
        )
        self.skill_q1 = create_skill(
            "破裂箭",
            kmbox_net.KEY_Q,
            cooldown=30 + 1,
            max_range=20,
        )
        self.skill_4 = create_skill(
            "瞄准箭",
            kmbox_net.KEY_4,
            cooldown=20 + 1,
            max_range=20,
            press_holdon=1.5,
        )
        self.skill_r = create_skill("狙击", kmbox_net.KEY_R)
        self.skill_t = create_skill("速射", kmbox_net.KEY_T, max_range=20)

        self.skill_e2.add_precondition_skills(self.skill_e1)
        self.skill_q1.add_precondition_skills(self.skill_1, self.skill_5)
        self.skill_4.add_precondition_skills(self.skill_e1)

    def search(self) -> None:
        if self.low_health():
            self.heal_self()

        _ = (
            self.skill_5.use(self.state.target_distance)
            or self.skill_1.use(self.state.target_distance)
            or self.skill_r.use(self.state.target_distance)
        )

    def combo_dodge(self) -> bool:
        return (
            self.skill_6.use(self.state.target_distance)
            or (
                self.skill_3.use(self.state.target_distance)
                and self.player_action.random_dodge(self, 1)
            )
            or self.player_action.random_dodge(self, 1)
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

        def check_and_dodge(_: int) -> bool:
            if self.too_close():
                return self.combo_dodge()
            return False

        def com_skill_q2(target_distance: int) -> bool:
            if self.skill_q2.can_use(target_distance) and self.state.is_signal_active(
                CombatSignal.LIWEIJIAN
            ):
                used = self.skill_q2.use(target_distance)
                if used:
                    self.state.consume_signal(CombatSignal.LIWEIJIAN)
                return used
            return False

        skills_to_use = [
            check_and_heal,
            check_and_dodge,
            com_skill_q2,
            self.skill_4.use,
            self.skill_e2.use,
            self.skill_q1.use,
        ]

        skills_to_use2 = [
            self.skill_e1.use,
            self.skill_2.use,
            self.skill_8.use,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skill_t.use)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(self.state.target_distance):
                return

        self.skill_1.use(self.state.target_distance)

    # def buff(self) -> None:
    #     pass
