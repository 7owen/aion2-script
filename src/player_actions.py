import random
import time

import kmbox_net

from console import console as console
from game_context import BotState, Box
from km_driver import KmboxDriver
from skill import Skill


class PlayerActions:
    """处理不区分职业的通用控制与交互动作。"""

    def __init__(self, km_driver: KmboxDriver):
        self.kmDriver = km_driver

        self.skill_f1 = Skill(
            "F1",
            kmbox_net.KEY_F1,
            self.kmDriver,
            cooldown=15,
            impact_time=2,
        )
        self.skill_space = Skill(
            "空格",
            kmbox_net.KEY_SPACEBAR,
            self.kmDriver,
            cooldown=1,
            time_consumption=0.5,
        )
        self.skill_shift = Skill(
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

    def heal(self, target_distance: int) -> bool:
        return self.skill_f1.use(target_distance)

    def dodge(self, target_distance: int) -> bool:
        if not self.skill_shift.is_can_use(target_distance):
            return False

        key = random.choice(self.move_keys)
        self.kmDriver.key_down(key)
        try:
            return self.skill_shift.use(target_distance)
        finally:
            self.kmDriver.key_up(key)

    def jump(self, target_distance: int) -> bool:
        return self.skill_space.use(target_distance)

    def random_walk(self) -> None:
        key = random.choice(self.move_keys)
        self.kmDriver.key_down(key)
        time.sleep(random.random())
        self.kmDriver.key_up(key)

    def press_interact(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_F)

    def rotate_view(self) -> None:
        self.kmDriver.mouse_left(True)
        time.sleep(random.random())
        self.kmDriver.human_mouse_move(random.choice([-1, 1]) * 600, 0, 0.5)
        time.sleep(random.random())
        self.kmDriver.mouse_left(False)

    def press_escape(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_ESCAPE)

    def open_inventory(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_I)

    def reset_mouse(self) -> None:
        self.kmDriver.mouse_reset()

    def move_mouse_to(self, x: int, y: int, duration: float = 0.5) -> None:
        self.kmDriver.human_mouse_move_to(x, y, duration)

    def click_left(self) -> None:
        self.kmDriver.mouse_left_press()

    def move_mouse_to_center(self) -> None:
        self.kmDriver.move_any_center()

    def loot(self) -> None:
        console.set_note_msg("拾取东西")
        self.press_interact()

    def extract_equipment(self, state: BotState) -> None:
        self.reset_mouse()
        self.press_escape()
        time.sleep(random.random())
        self.open_inventory()
        time.sleep(random.random())
        self.move_mouse_to(
            random.randint(1735, 1785),
            random.randint(1025, 1060),
            0.5,
        )
        self.click_left()
        time.sleep(random.random())
        self.move_mouse_to(
            random.randint(1616, 1720),
            random.randint(972, 998),
            0.3,
        )
        time.sleep(random.random())
        self.click_left()
        time.sleep(random.random())
        self.press_interact()
        time.sleep(random.random())
        self.press_interact()
        time.sleep(1)
        self.press_interact()
        time.sleep(random.random())
        self.press_escape()
        time.sleep(random.random())
        self.move_mouse_to_center()
        state.schedule_next_extract()

    def resurrect_character(self, state: BotState) -> None:
        btn_box = state.resurrection_box
        if btn_box is None:
            return

        self.reset_mouse()
        self.move_mouse_to(
            random.randint(btn_box[0] + 5, btn_box[2] - 5),
            random.randint(btn_box[1] + 5, btn_box[3] - 5),
            1,
        )
        time.sleep(random.random())
        self.click_left()
        state.resurrection_box = None
