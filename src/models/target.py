from .buff import Buff
from .creature import Creature
from .skill_data import TARGET_BUFFS


class Target(Creature):
    """当前选中的目标"""

    def __init__(self):
        super().__init__()
        self.distance: int = -1
        self.has_target: bool = False

        for buff_code in TARGET_BUFFS:
            self.buffs[buff_code] = Buff(TARGET_BUFFS[buff_code])

    def clear(self) -> None:
        self.distance = -1
        self.has_target = False
        for buff_code in self.buffs:
            self.buffs[buff_code].clear()
