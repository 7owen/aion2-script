import random
import time

import kmbox_net

from bot_config import RoleConfig
from role import Role, Skill


class RoleSwordStar(Role):
    def __init__(
        self,
        role_config: RoleConfig,
        km_driver,
    ) -> None:
        super().__init__(config=role_config, km_driver=km_driver)
        self.skill_1 = Skill(
            "跳跃攻击",
            kmbox_net.KEY_1,
            self.kmDriver,
            cooldown=15,
            time_consumption=1,
        )
        self.skill_2 = Skill(
            "蹂躏剑",
            kmbox_net.KEY_2,
            self.kmDriver,
            cooldown=20,
            range=4,
            time_consumption=3,
            impact_time=4,
        )
        self.skill_3 = Skill(
            "粉碎波动",
            kmbox_net.KEY_3,
            self.kmDriver,
            cooldown=20,
            range=4,
            time_consumption=1,
            press_count=2,
            press_interval=0.5,
        )
        self.skill_4 = Skill(
            "破灭猛击", kmbox_net.KEY_4, self.kmDriver, cooldown=30, time_consumption=1
        )
        self.skill_5 = Skill(
            "愤怒波动",
            kmbox_net.KEY_5,
            self.kmDriver,
            cooldown=60,
            range=4,
            impact_time=3,
            time_consumption=0.5,
        )
        self.skill_6 = Skill(
            "强袭一击",
            kmbox_net.KEY_6,
            self.kmDriver,
            cooldown=120,
            impact_time=3,
            time_consumption=0.5,
        )
        self.skill_7 = Skill(
            "毅力",
            kmbox_net.KEY_7,
            self.kmDriver,
            cooldown=150,
            time_consumption=1,
        )

        self.skill_e1 = Skill(
            "脚踝斩",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=10,
            range=4,
            impact_time=3,
            time_consumption=0.5,
        )
        self.skill_r = Skill(
            "锐利一击",
            kmbox_net.KEY_R,
            self.kmDriver,
        )
        self.skill_t = Skill(
            "斩断猛击",
            kmbox_net.KEY_T,
            self.kmDriver,
            range=4,
        )

        self.skill_q2 = Skill(
            "突进一击",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=20,
            range=6,  # 实际范围是10米，为了走进再触发技能
            impact_time=3,
            time_consumption=1,
        )

        self.skill_q1 = Skill(
            "空中结缚",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=45,
            range=4,
            impact_time=3,
            time_consumption=0.5,
            precondition_skills=[
                self.skill_2,
                self.skill_q2,
                self.skill_6,
                self.skill_5,
            ],
        )

        self.skill_e2 = Skill(
            "下盘击",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=5,
            range=4,
            time_consumption=0.5,
            precondition_skills=[
                self.skill_2,
                self.skill_q2,
                self.skill_6,
                self.skill_5,
            ],
        )

    def search(self):
        if self.check_low_health():
            self.dodge()
            self.heal()

        _ = (
            self.skill_1.use(self.target_distance)
            or self.skill_4.use(self.target_distance)
            or self.skill_6.use(self.target_distance)
            or self.skill_r.use(self.target_distance)
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

        def com_skil_q2(target_distance):
            if self.skill_q2.is_can_use(self.target_distance):
                self._dodge()
                self.skill_q2.use(target_distance)

        # 格挡无法检测，只要冷却就1/2机率按键释放
        def com_skil_e1(target_distance):
            if self.skill_e1.is_can_use(target_distance) and random.randint(0, 1) == 0:
                return self.skill_e1.use(target_distance)
            return False

        skills_to_use = [
            check_and_heal,
            check_and_dodge,
            self.skill_q1.use,
            self.skill_e2.use,
            com_skil_q2,
            com_skil_e1,
            self.skill_q2.use,
        ]
        skills_to_use2 = [
            self.skill_1.use,
            self.skill_2.use,
            self.skill_3.use,
            self.skill_5.use,
            self.skill_6.use,
            self.skill_t.use,
        ]
        random.shuffle(skills_to_use2)
        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(self.target_distance):
                return

        self.skill_1.use(self.target_distance)

    def buff(self):
        self.skill_7.use(self.target_distance)

    def dodge(self):
        pass

    def _need_random_jump_distance(self):
        if self.target_distance == -1 or self.target_distance <= 20:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True

    def _need_random_walk_distance(self):
        if self.target_distance == -1 or self.target_distance > 4:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True
