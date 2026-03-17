import random
import time

import kmbox_net

from console import console as console
from game_context import GameContext
from km_driver import KmboxDriver
from skill import Skill


class PlayerController:
    """处理不区分职业的通用玩家行为，如拾取、复活、开包、转视角等"""

    def __init__(self, km_driver: KmboxDriver, context: GameContext):
        self.kmDriver = km_driver
        self.context = context

        # 通用技能初始化（回血、跳跃、闪避）
        self.skill_f1 = Skill(
            "F1", kmbox_net.KEY_F1, self.kmDriver, cooldown=15, impact_time=2
        )
        self.skill_space = Skill(
            "空格",
            kmbox_net.KEY_SPACEBAR,
            self.kmDriver,
            cooldown=1,
            time_consumption=0.5,
        )
        self.skill_sifht = Skill(
            "紧急回避",
            kmbox_net.KEY_LEFTSHIFT,
            self.kmDriver,
            cooldown=1,
            impact_time=1,
        )

        self.move_keys = [
            kmbox_net.KEY_A,
            kmbox_net.KEY_D,
            kmbox_net.KEY_S,
        ]

    def heal(self):
        console.set_note_msg(f"恢复生命, 剩余{self.context.health * 100:.2f}%")
        return self.skill_f1.use(self.context.target_distance)

    def dodge(self):
        key = random.choice(self.move_keys)
        self.kmDriver.key_down(key)
        self.skill_sifht.use(self.context.target_distance)
        self.kmDriver.key_up(key)

    def jump(self):
        return self.skill_space.use(self.context.target_distance)

    def random_walk(self):
        key = random.choice(self.move_keys)
        self.kmDriver.key_down(key)
        time.sleep(random.random())
        self.kmDriver.key_up(key)

    def loot(self):
        console.set_note_msg("拾取东西")
        self.kmDriver.key_press(kmbox_net.KEY_F)

    def rotate_view(self):
        self.kmDriver.key_press(kmbox_net.KEY_KEYPAD_MINUS)
        # self.kmDriver.mouse_left(True)
        time.sleep(random.random())
        self.kmDriver.human_mouse_move(random.choice([-1, 1]) * 600, 0, 0.5)
        time.sleep(random.random())
        # self.kmDriver.mouse_left(False)
        self.kmDriver.key_press(kmbox_net.KEY_KEYPAD_MINUS)

    def extraction(self):
        self.kmDriver.mouse_reset()
        self.kmDriver.key_press(kmbox_net.KEY_ESCAPE)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_I)
        time.sleep(random.random())
        self.kmDriver.human_mouse_move_to(
            random.randint(1735, 1785), random.randint(1025, 1060), 0.5
        )
        self.kmDriver.mouse_left_press()
        time.sleep(random.random())
        self.kmDriver.human_mouse_move_to(
            random.randint(1616, 1720), random.randint(972, 998), 0.3
        )
        time.sleep(random.random())
        self.kmDriver.mouse_left_press()
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(1)
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_ESCAPE)
        time.sleep(random.random())
        self.kmDriver.move_any_center()
        self.context.extract_countdowning()

    def resurrect(self, btn_box):
        if btn_box is None:
            return
        self.kmDriver.mouse_reset()
        self.kmDriver.human_mouse_move_to(
            random.randint(btn_box[0] + 5, btn_box[2] - 5),
            random.randint(btn_box[1] + 5, btn_box[3] - 5),
            1,
        )
        time.sleep(random.random())
        self.kmDriver.mouse_left_press()
