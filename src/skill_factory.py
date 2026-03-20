from km_driver import KmboxDriver
from skill import Skill


class SkillFactory:
    def __init__(self, km_driver: KmboxDriver) -> None:
        self.km_driver = km_driver

    def create_skill(
        self,
        name: str,
        key: int,
        *,
        cooldown: float = 0,
        max_range: int | None = None,
        time_consumption: float = 0.5,
        press_holdon: float | None = None,
        impact_time: float = 0,
        press_count: int = 1,
        press_interval: float = 0.5,
    ) -> Skill:
        return Skill(
            name=name,
            key=key,
            km_driver=self.km_driver,
            cooldown=cooldown,
            max_range=max_range,
            time_consumption=time_consumption,
            press_holdon=press_holdon,
            impact_time=impact_time,
            press_count=press_count,
            press_interval=press_interval,
        )
