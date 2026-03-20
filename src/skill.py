import time
import weakref

from km_driver import KmboxDriver


class Skill:
    def __init__(
        self,
        name: str,
        key: int,
        km_driver: KmboxDriver,
        cooldown: float,
        max_range: int | None,
        time_consumption: float,
        press_holdon: float | None,
        impact_time: float,
        press_count: int,
        press_interval: float,
    ):
        self.name = name
        self.kmDriver = km_driver
        self.key = key
        self.cooldown = cooldown
        self.max_range = max_range
        self.time_consumption = time_consumption
        self.press_holdon = press_holdon
        self.impact_time = impact_time
        self.press_count = press_count
        self.press_interval = press_interval
        self.precondition_skills = []
        self.mutual_exclusion_skills = []
        self.last_used_at = 0.0
        self.impact_until = 0.0

    def add_precondition_skills(self, *skills):
        for skill in skills:
            if not isinstance(skill, Skill):
                raise TypeError("precondition_skills must be a Skill instance")
            self.precondition_skills.append(weakref.ref(skill))

    def add_mutual_exclusion_skills(self, *skills):
        for skill in skills:
            if not isinstance(skill, Skill):
                raise TypeError("mutual_exclusion_skill must be a Skill instance")
            self.mutual_exclusion_skills.append(weakref.ref(skill))

    def is_ready(self) -> bool:
        return self.get_remaining_cd() <= 0

    def get_remaining_cd(self) -> float:
        elapsed = time.monotonic() - self.last_used_at
        return max(0, self.cooldown - elapsed)

    def can_use(self, target_distance: int) -> bool:
        if not self.is_ready():
            return False

        if self.max_range is not None and not (0 <= target_distance <= self.max_range):
            return False

        if any(
            (s := weak_skill()) and s.is_impacting()
            for weak_skill in self.mutual_exclusion_skills
        ):
            return False

        if not self.precondition_skills:
            return True

        return any(
            (s := weak_skill()) and s.is_impacting()
            for weak_skill in self.precondition_skills
        )

    def is_impacting(self) -> bool:
        return time.monotonic() < self.impact_until

    def use(self, target_distance: int) -> bool:
        if not self.can_use(target_distance):
            return False

        now = time.monotonic()
        self.last_used_at = now
        for i in range(self.press_count):
            self._press_once()
            if i < self.press_count - 1:
                time.sleep(self.press_interval)

        wait_time = self.time_consumption - (time.monotonic() - now)
        if wait_time > 0:
            time.sleep(wait_time)

        self.impact_until = time.monotonic() + self.impact_time
        return True

    def _press_once(self) -> None:
        if self.press_holdon is not None:
            self.kmDriver.key_press(self.key, self.press_holdon)
        else:
            self.kmDriver.key_press(self.key)
