import random

import kmbox_net

from bot_config import RoleConfig
from role import Aion2Role, Skill


class Aion2RoleSwordStar(Aion2Role):
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
            time_consumption=2,
            impact_time=3,
        )
        self.skill_3 = Skill(
            "粉碎波动",
            kmbox_net.KEY_3,
            self.kmDriver,
            cooldown=20,
            range=4,
            time_consumption=2,
        )
        self.skill_4 = Skill(
            "破灭猛击",
            kmbox_net.KEY_4,
            self.kmDriver,
            cooldown=30,
            time_consumption=1,
        )
        self.skill_5 = Skill(
            "愤怒波动",
            kmbox_net.KEY_5,
            self.kmDriver,
            cooldown=60,
            range=4,
            time_consumption=1,
        )
        self.skill_6 = Skill(
            "强袭一击",
            kmbox_net.KEY_6,
            self.kmDriver,
            cooldown=120,
            time_consumption=1,
        )
        self.skill_7 = Skill(
            "毅力",
            kmbox_net.KEY_7,
            self.kmDriver,
            cooldown=150,
            time_consumption=1,
        )

        self.skill_q1 = Skill(
            "空中结缚",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=5,
            range=4,
            time_consumption=2,
        )
        self.skill_q2 = Skill(
            "突进一击",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=20,
            range=10,
            time_consumption=1,
        )
        self.skill_e1 = Skill(
            "脚踝斩",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=5,
            range=4,
            time_consumption=2,
        )
        self.skill_e2 = Skill(
            "下盘击",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=5,
            range=4,
            time_consumption=2,
        )
        self.skill_r = Skill(
            "锐利一击",
            kmbox_net.KEY_R,
            self.kmDriver,
            cooldown=0.2,
            time_consumption=2,
        )
        self.skill_t = Skill(
            "斩断猛击",
            kmbox_net.KEY_T,
            self.kmDriver,
            cooldown=0.2,
            range=4,
            time_consumption=2,
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
        if self.check_low_health():
            self.dodge()
            self.heal()

        if self.check_is_close():
            self.dodge()

        if self.skill_e2.is_can_use(self.target_distance) and (
            self.skill_2.is_impacting() or self.skill_q2.is_impacting()
        ):
            self.skill_e2.use(self.target_distance)

        if self.skill_q1.is_can_use(self.target_distance) and (
            self.skill_2.is_impacting() or self.skill_q2.is_impacting()
        ):
            self.skill_q1.use(self.target_distance)

        if (
            self.skill_q2.is_can_use(self.target_distance)
            and self.skill_sifht.is_impacting()
        ):
            self.skill_q2.use(self.target_distance)

        if self.skill_e1.is_can_use(self.target_distance) and random.randint(0, 4) == 0:
            self.skill_e1.use(self.target_distance)

        skills_to_use = [
            self.skill_1,
            self.skill_2,
            self.skill_3,
            self.skill_4,
            self.skill_5,
            self.skill_6,
        ]
        random.shuffle(skills_to_use)
        for skill in skills_to_use:
            skill.use(self.target_distance)

        if random.randint(0, 1) == 0:
            self.skill_t.use(self.target_distance)

    def buff(self):
        self.skill_7.use(self.target_distance)

    def dodge(self):
        if self.skill_q2.is_can_use(self.target_distance):
            self._dodge()
