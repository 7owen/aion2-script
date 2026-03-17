import time
import weakref

from km_driver import KmboxDriver


class Skill:
    def __init__(
        self,
        name: str,
        key: int,
        km_driver: KmboxDriver,
        cooldown: float = 0,
        range: int | None = None,
        time_consumption: float = 0,
        press_holdon: float | None = None,
        impact_time: float = 0,
        press_count: int = 1,
        press_interval: float = 0,
    ):
        self.name = name
        self.kmDriver = km_driver
        self.key = key
        self.cooldown = cooldown
        self.rang = range
        self.time_consumption = time_consumption
        self.press_holdon = press_holdon
        self.impact_time = impact_time
        self.press_count = press_count
        self.press_interval = press_interval
        self.precondition_skill = []
        self.mutual_exclusion_skills = []
        self.last_used_at = float("-inf")
        self.impact_until = float("-inf")
        if self.kmDriver is None:
            raise ValueError("Skill requires a valid km_driver instance")

    def add_precondition_skills(self, *skills):
        for skill in skills:
            if not isinstance(skill, Skill):
                raise TypeError("precondition_skill must be a Skill instance")
            self.precondition_skill.append(weakref.ref(skill))

    def add_mutual_exclusion_skills(self, *skills):
        for skill in skills:
            if not isinstance(skill, Skill):
                raise TypeError("mutual_exclusion_skill must be a Skill instance")
            self.mutual_exclusion_skills.append(weakref.ref(skill))

    def is_off_cooldown(self) -> bool:
        return self.get_remaining_cd() <= 0

    def get_remaining_cd(self) -> float:
        elapsed = time.monotonic() - self.last_used_at
        return max(0, self.cooldown - elapsed)

    def is_can_use(self, target_distance: int) -> bool:
        if not self.is_off_cooldown():
            return False

        if self.rang is not None and (
            target_distance < 0 or target_distance > self.rang
        ):
            return False

        if any(skill().is_impacting() for skill in self.mutual_exclusion_skills):
            return False

        if not self.precondition_skill:
            return True

        return any(skill().is_impacting() for skill in self.precondition_skill)

    def is_impacting(self) -> bool:
        return time.monotonic() < self.impact_until

    def use(self, target_distance) -> bool:
        if not self.is_can_use(target_distance):
            return False

        self.last_used_at = time.monotonic()
        for i in range(self.press_count):
            self._press_once()
            if i < self.press_count - 1:
                time.sleep(self.press_interval)

        time.sleep(self.time_consumption)
        self.impact_until = time.monotonic() + self.impact_time
        return True

    def _press_once(self) -> None:
        if self.press_holdon is not None:
            self.kmDriver.key_press(self.key, self.press_holdon)
        else:
            self.kmDriver.key_press(self.key)
