import random
import time

import kmbox_net

from bot_config import RoleConfig
from role import Role
from skill import Skill


class RoleSwordStar(Role):
    def __init__(
        self,
        role_config: RoleConfig,
        km_driver,
        player_ctrl,
        context,
    ) -> None:
        super().__init__(
            config=role_config,
            km_driver=km_driver,
            player_ctrl=player_ctrl,
            context=context,
        )
        self.skill_1 = Skill(
            "跳跃攻击",
            kmbox_net.KEY_1,
            self.kmDriver,
            cooldown=15 + 1,
            # time_consumption=0.5,
        )

        self.skill_2 = Skill(
            "蹂躏剑",
            kmbox_net.KEY_2,
            self.kmDriver,
            cooldown=20 + 1,
            range=4,
            time_consumption=1.5,
            impact_time=3,
        )

        self.skill_3 = Skill(
            "粉碎波动",
            kmbox_net.KEY_3,
            self.kmDriver,
            cooldown=20 + 1,
            range=4,
            time_consumption=1,
            press_count=2,
            press_interval=0.3,
        )

        self.skill_4 = Skill(
            "破灭猛击",
            kmbox_net.KEY_4,
            self.kmDriver,
            cooldown=30,
            time_consumption=0.5,
        )

        self.skill_5 = Skill(
            "愤怒波动",
            kmbox_net.KEY_5,
            self.kmDriver,
            cooldown=60 + 1,
            range=4,
            impact_time=3,
            time_consumption=0.5,
        )
        self.skill_6 = Skill(
            "强袭一击",
            kmbox_net.KEY_6,
            self.kmDriver,
            cooldown=120 + 1,
            impact_time=3,
            time_consumption=0.5,
        )

        self.skill_7 = Skill(
            "激怒爆炸",
            kmbox_net.KEY_7,
            self.kmDriver,
            cooldown=45 + 1,
            range=4,
            time_consumption=0.5,
            impact_time=10,
        )

        self.skill_e1 = Skill(
            "脚踝斩",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=10 + 1,
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
            cooldown=20 + 1,
            range=10,  # 实际范围是10米，为了走进再触发技能
            impact_time=3,
            press_holdon=0.5,
            time_consumption=1,
        )

        self.skill_q1 = Skill(
            "空中结缚",
            kmbox_net.KEY_Q,
            self.kmDriver,
            cooldown=45 + 1,
            range=4,
            impact_time=3,
            time_consumption=0.5,
        )

        self.skill_e2 = Skill(
            "下盘击",
            kmbox_net.KEY_E,
            self.kmDriver,
            cooldown=5 + 1,
            range=4,
            time_consumption=0.5,
        )

        self.skill_q1.add_precondition_skills(
            self.skill_2, self.skill_q2, self.skill_6, self.skill_5, self.skill_7
        )

        self.skill_e2.add_precondition_skills(
            self.skill_2, self.skill_q2, self.skill_6, self.skill_5, self.skill_7
        )

    def search(self):
        if self.check_low_health():
            self.dodge()
            self.player_ctrl.heal()

        _ = (
            self.skill_1.use(self.context.target_distance)
            or self.skill_4.use(self.context.target_distance)
            or self.skill_6.use(self.context.target_distance)
            or self.skill_r.use(self.context.target_distance)
        )

    def fight(self):
        if self._need_random_jump_distance():
            self.player_ctrl.jump()

        if self._need_random_walk_distance():
            self.player_ctrl.random_walk()

        def check_and_heal(target_distance):
            if self.check_low_health():
                return self.player_ctrl.heal() and self.player_ctrl.dodge()
            return False

        # def check_and_dodge(target_distance):
        #     if self.check_is_close():
        #         return self.dodge()
        #     return False

        def com_skil_q2(target_distance):
            if self.skill_q2.is_can_use(self.context.target_distance):
                self.player_ctrl.dodge()
                self.skill_q2.use(target_distance)

        # 格挡无法检测，只要冷却就1/2机率按键释放
        def com_skil_e1(target_distance):
            if self.skill_e1.is_can_use(target_distance) and random.randint(0, 1) == 0:
                return self.skill_e1.use(target_distance)
            return False

        skills_to_use = [
            check_and_heal,
            self.skill_q1.use,  # 空中束缚
            self.skill_e2.use,  # 下盘击
            # com_skil_e1,  # 随机格挡触发
            self.skill_3.use,
        ]
        skills_to_use2 = [
            self.skill_6.use,
            self.skill_5.use,
            self.skill_7.use,
            self.skill_2.use,  # 选择一个击倒技能
            com_skil_q2,
        ]
        random.shuffle(skills_to_use2)
        skills_to_use2.append(self.skill_t.use)

        for skill_use in skills_to_use + skills_to_use2:
            if skill_use(self.context.target_distance):
                return

        self.skill_1.use(self.context.target_distance)

    def buff(self):
        # self.skill_7.use(self.context.target_distance)
        pass

    def dodge(self):
        pass

    def _need_random_jump_distance(self):
        if self.context.target_distance <= 20:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True

    def _need_random_walk_distance(self):
        if self.context.target_distance < 0 or self.context.target_distance > 4:
            return False
        if random.randint(0, 3) != 1:
            return False
        return True
