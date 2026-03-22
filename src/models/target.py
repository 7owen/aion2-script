from .buff import Buff
from .creature import Creature
from .skill_data import TARGET_BUFFS


class Target(Creature):
    """当前选中的目标"""

    def __init__(self):
        super().__init__()
        self.distance: int = -1
        self.has_target: bool = False

        for buff_metadata in TARGET_BUFFS:
            self.buffs[buff_metadata.code] = Buff(buff_metadata)

    def set_has_target(self, distance: int) -> None:
        self.has_target = True
        if distance >= 0:
            self.distance = distance

    def clear_target(self) -> None:
        self.distance = -1
        self.has_target = False
        self.clear_buffs()
