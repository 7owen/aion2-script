import random
import time
from abc import ABC, abstractmethod

import kmbox_net

from bot_config import RoleConfig
from console import console as console
from km_driver import KmboxDriver


class Skill:
    recent_skills: list[str] = []

    def __init__(
        self,
        name: str,
        key: int,
        km_driver: KmboxDriver,
        cooldown: float | None = None,
        range: int | None = None,
        time_consumption: float = 0.3,
        press_holdon: float | None = None,
        impact_time: float = 0,
    ):
        self.name = name
        self.kmDriver = km_driver
        self.key = key
        self.cooldown = cooldown
        self.rang = range
        self.time_consumption = time_consumption
        self.press_holdon = press_holdon
        self.impact_time = impact_time
        self.last_used_at = float("-inf")
        self.impact_until = float("-inf")
        if self.kmDriver is None:
            raise ValueError("Skill requires a valid km_driver instance")

    def is_off_cooldown(self) -> bool:
        if self.cooldown is None:
            return True
        return self.get_remaining_cd() <= 0

    def get_remaining_cd(self) -> float:
        if self.cooldown is None:
            return 0
        elapsed = time.monotonic() - self.last_used_at
        return max(0, self.cooldown - elapsed)

    def is_can_use(self, target_distance: int) -> bool:
        if not self.is_off_cooldown():
            return False
        if self.rang is None:
            return True

        return target_distance != -1 and self.rang >= target_distance

    def is_impacting(self) -> bool:
        return time.monotonic() < self.impact_until

    def use(self, target_distance) -> bool:
        if not self.is_can_use(target_distance):
            return False

        Skill.recent_skills.append(self.name)
        if len(Skill.recent_skills) > 10:
            Skill.recent_skills.pop(0)

        now = time.monotonic()
        self.last_used_at = now
        self.impact_until = now + self.impact_time
        if self.press_holdon:
            self.kmDriver.key_press(self.key, int(self.press_holdon * 1000))
        else:
            self.kmDriver.key_press(self.key)

        time.sleep(self.time_consumption)
        return True


class Aion2Role(ABC):
    def __init__(
        self,
        km_driver: KmboxDriver,
        config: RoleConfig,
    ) -> None:
        self.config = config
        self.health = 1.0
        self.mental = 1.0
        self.has_target = False
        self.target_distance = -1
        self.need_extract = False
        self.next_extract_at = float("inf")
        self._started = False

        self.kmDriver = km_driver
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
            time_consumption=0.5,
            impact_time=1,
        )

    def start(self):
        self._started = True
        self.next_extract_at = time.monotonic() + self.config.extract_interval_seconds

    def stop(self):
        if self._started:
            self._started = False
        self.kmDriver.close()

    def tick(self):
        if not self._started:
            self.start()
        now = time.monotonic()
        if now >= self.next_extract_at:
            self.need_extract = True
            self.next_extract_at = now + self.config.extract_interval_seconds

    @abstractmethod
    def search(self):
        pass

    @abstractmethod
    def fight(self):
        pass

    @abstractmethod
    def buff(self):
        pass

    def loot(self):
        console.set_note_msg("拾取东西")
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(0.2)

    def heal(self):
        console.set_note_msg(f"恢复生命, 剩余{self.health * 100:.2f}%")
        return self.skill_f1.use(self.target_distance)

    def is_low_health(self):
        return self.health != -1 and self.health < self.config.low_health_threshold

    def check_low_health(self):
        if self.is_low_health():
            # console.set_note_msg("生命值低")
            return True
        return False

    def is_close(self):
        return (
            self.target_distance != -1
            and self.target_distance <= self.config.close_distance_threshold
        )

    def check_is_close(self):
        if self.is_close():
            console.set_note_msg("距离目标太近")
            return True
        return False

    def get_skill_cd_info(self):
        cd_parts = []
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, Skill):
                is_off_cd = attr_value.is_off_cooldown()
                status_color = "green" if is_off_cd else "red"
                if is_off_cd:
                    cd_parts.append(f"[{status_color}]{attr_value.name}[/]")
                else:
                    remaining = attr_value.get_remaining_cd()
                    cd_parts.append(
                        f"[{status_color}]{attr_value.name}({remaining:.1f}s)[/]"
                    )

        return " | ".join(cd_parts)

    def get_recent_skills(self):
        return " -> ".join([f"[bold cyan]{name}[/]" for name in Skill.recent_skills])

    keys = [
        kmbox_net.KEY_A,
        kmbox_net.KEY_D,
        kmbox_net.KEY_S,
        kmbox_net.KEY_W,
    ]

    def _dodge(self):
        key = random.choice(self.keys)
        self.kmDriver.key_down(key)
        self.skill_sifht.use(self.target_distance)
        self.kmDriver.key_up(key)

    def _random_jump(self):
        if self.target_distance == -1 or self.target_distance <= 20:
            return
        if random.randint(0, 3) != 1:
            return
        self.skill_space.use(self.target_distance)

    def _random_walk(self):
        if self.target_distance == -1 or self.target_distance > 20:
            return
        if random.randint(0, 3) != 1:
            return
        key = random.choice(self.keys)
        self.kmDriver.key_down(key)
        time.sleep(random.random())
        self.kmDriver.key_up(key)

    def rotate_view(self):
        self.kmDriver.mouse_left(True)
        time.sleep(1)
        self.kmDriver.mouse_move_auto(-500, 0, 0.5, False)
        time.sleep(0.2)
        self.kmDriver.mouse_left(False)
        time.sleep(0.2)

    def extraction(self):
        self.kmDriver.key_press(kmbox_net.KEY_I)
        time.sleep(0.5)
        self.kmDriver.human_mouse_move_to(
            random.randint(1735, 1785), random.randint(1025, 1060), 0.5
        )
        self.kmDriver.mouse_left_press()
        time.sleep(0.5)
        self.kmDriver.human_mouse_move_to(
            random.randint(1616, 1720), random.randint(972, 998), 0.3
        )
        self.kmDriver.mouse_left_press()
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_F)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_ESCAPE)
        time.sleep(random.random())
        self.kmDriver.key_press(kmbox_net.KEY_ESCAPE)
        self.kmDriver.human_mouse_move_to(
            random.randint(900, 1000), random.randint(500, 600), 0.5
        )
        self.need_extract = False
        self.next_extract_at = time.monotonic() + self.config.extract_interval_seconds

    def resurrect(self, btn_box):
        if btn_box is None:
            return
        print(f"resurrect: {btn_box}")
        print(
            f"{random.randint(btn_box[0] + 5, btn_box[2] - 5)}, {random.randint(btn_box[1] + 5, btn_box[3] - 5)}"
        )
        self.kmDriver.human_mouse_move_to(
            random.randint(btn_box[0] + 5, btn_box[2] - 5),
            random.randint(btn_box[1] + 5, btn_box[3] - 5),
            1,
        )
        time.sleep(random.random())
        self.kmDriver.mouse_left_press()
