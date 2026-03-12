import random
import time

import kmbox_net

from bot_config import RoleConfig
from role import Role, Skill


class RoleBowStar(Role):
    def __init__(
        self,
        role_config: RoleConfig,
        km_driver,
    ) -> None:
        super().__init__(config=role_config, km_driver=km_driver)
        self.skill_1 = Skill(
            "套索箭", kmbox_net.KEY_1, self.kmDriver, cooldown=15, impact_time=5
        )
        self.skill_2 = Skill(
            "疯狂箭",
            kmbox_net.KEY_2,
            self.kmDriver,
            cooldown=20,
            range=20,
            press_holdon=0.5,
        )
        self.skill_3 = Skill(
            "爆炸圈套",
            kmbox_net.KEY_3,
            self.kmDriver,
            cooldown=20,
            range=20,
            time_consumption=1,
        )
        self.skill_5 = Skill(
            "箭失风暴", kmbox_net.KEY_5, self.kmDriver, cooldown=60, impact_time=10
        )
        self.skill_6 = Skill(
            "突击踢",
            kmbox_net.KEY_6,
            self.kmDriver,
            cooldown=30,
            range=10,
            time_consumption=1,
        )
        self.skill_7 = Skill(
            "白什么灌能",
            kmbox_net.KEY_7,
            self.kmDriver,
            cooldown=60,
            time_consumption=1,
        )
        self.skill_8 = Skill(
            "爆炸箭",
            kmbox_net.KEY_8,
            self.kmDriver,
            cooldown=45,
            range=20,
            time_consumption=0.5,
        )

        self.skill_q2 = Skill(
            "利锥箭", kmbox_net.KEY_Q, self.kmDriver, cooldown=5, range=20
        )
        self.skill_e1 = Skill(
            "目标箭",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=10,
            range=20,
            impact_time=10,
        )
        self.skill_e2 = Skill(
            "压制箭",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=3,
            range=20,
            impact_time=5,
            precondition_skills=[self.skill_e1],
        )
        self.skill_q1 = Skill(
            "破裂箭",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=30,
            range=20,
            precondition_skills=[self.skill_1, self.skill_5],
        )
        self.skill_4 = Skill(
            "瞄准箭",
            kmbox_net.KEY_4,
            self.kmDriver,
            cooldown=20,
            range=20,
            press_holdon=1.5,
            precondition_skills=[self.skill_e1],
        )
        self.skill_r = Skill("狙击", kmbox_net.KEY_R, self.kmDriver)
        self.skill_t = Skill("速射", kmbox_net.KEY_T, self.kmDriver, range=20)

    def search(self):
        if self.check_low_health():
            _ = self.heal() and self._dodge()

        _ = (
            self.skill_5.use(self.target_distance)
            or self.skill_1.use(self.target_distance)
            or self.skill_r.use(self.target_distance)
        )

    def dodge(self):
        _ = (
            self.skill_6.use(self.target_distance)
            or (self.skill_3.use(self.target_distance) and self._dodge())
            or self._dodge()
        )

    def fight(self):
        self._random_jump()

        self._random_walk()

        def check_and_heal(target_distance):
            if self.check_low_health():
                return self.heal() and self._dodge()
            return False

        def check_and_dodge(target_distance):
            if self.check_is_close():
                return self.dodge()
            return False

        if self.skill_q2.is_can_use(self.target_distance) and random.randint(0, 1) == 0:
            self.skill_q2.use(self.target_distance)

        skills_to_use = [
            check_and_heal,
            check_and_dodge,
            self.skill_e1.use,
            self.skill_e2.use,
            self.skill_q1.use,
            self.skill_4.use,
        ]
        skills_to_use2 = [
            self.skill_2.use,
            self.skill_8.use,
            self.skill_t.use,
        ]
        random.shuffle(skills_to_use2)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(self.target_distance):
                return

        self.skill_1.use(self.target_distance)

    def buff(self):
        pass
        # self.skill_7.use(self.target_distance)
        #

    def _need_random_jump_distance(self):
        if self.target_distance == -1 or self.target_distance <= 20:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True

    def _need_random_walk_distance(self):
        if self.target_distance == -1 or self.target_distance > 20:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True
