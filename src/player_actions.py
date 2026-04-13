import random
import time

import kmbox_net

from console import console as console
from km_driver import KmboxDriver


class PlayerActions:
    """处理不区分职业的通用控制与交互动作。"""

    def __init__(self, km_driver: KmboxDriver):
        self.kmDriver = km_driver

        self.move_keys = [
            kmbox_net.KEY_A,
            kmbox_net.KEY_S,
        ]

        self.dodge_keys = [
            kmbox_net.KEY_A,
            kmbox_net.KEY_D,
            kmbox_net.KEY_S,
        ]

    def random_jump(self, role, probability: float) -> bool:
        if random.random() > probability:
            return False
        return role.jump()

    def random_dodge(self, role, probability: float) -> bool:
        if random.random() > probability:
            return False

        key = random.choice(self.dodge_keys)
        self.kmDriver.key_down(key)
        time.sleep(0.1)
        role.dodge()
        time.sleep(0.1)
        # self.kmDriver.key_press(kmbox_net.KEY_LEFTSHIFT)
        self.kmDriver.key_up(key)
        return True

    def random_walk(self, probability: float) -> bool:
        if random.random() > probability:
            return False

        key = random.choice(self.move_keys)
        self.kmDriver.key_down(key)
        time.sleep(random.random())
        self.kmDriver.key_up(key)
        return True

    def press_confirm(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_F)

    def rotate_view(self) -> None:
        self.kmDriver.mouse_left(True)
        time.sleep(random.random())
        self.kmDriver.human_mouse_move(random.choice([-1, 1]) * 600, 0, 0.5)
        time.sleep(random.random())
        self.kmDriver.mouse_left(False)

    def searching_enemy(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_TAB)
        # self.kmDriver.key_press(kmbox_net.KEY_R)
        time.sleep(0.3)

    def hold_normal_fight_key(self) -> None:
        self.kmDriver.key_down(kmbox_net.KEY_R)

    def release_normal_fight_key(self) -> None:
        self.kmDriver.key_up(kmbox_net.KEY_R)

    def press_escape(self) -> None:
        self.kmDriver.key_press(kmbox_net.KEY_TAB)
        time.sleep(0.3)

    def click_inventory(self) -> None:
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
        self.press_confirm()

    def extract_equipment(self) -> None:
        self.reset_mouse()
        # self.press_escape()
        # time.sleep(random.random())
        self.click_inventory()
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
        self.press_confirm()
        time.sleep(random.random())
        self.press_confirm()
        # time.sleep(random.random())
        time.sleep(2)
        self.press_confirm()
        # time.sleep(random.random())
        time.sleep(1)
        self.click_inventory()
        # self.press_escape()
        time.sleep(random.random())
        self.move_mouse_to_center()

    def resurrect_character(self, btn_box) -> None:
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
        time.sleep(1 + random.random())
