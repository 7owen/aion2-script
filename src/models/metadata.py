class GameEntity:
    """游戏实体元数据基类，用于Buff、Skill等公共属性"""

    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.code == other
        if isinstance(other, GameEntity):
            return self.code == other.code
        return False


class BuffMetadata(GameEntity):
    """Buff元数据"""

    def __init__(self, code: str, name: str, duration: float):
        super().__init__(code=code, name=name)
        self.duration = duration


class SkillMetadata(GameEntity):
    """技能元数据"""

    def __init__(
        self,
        code: str,
        name: str,
        key: int,
        cooldown: float = 0.0,
        max_range: int | None = None,
        time_consumption: float = 0.5,
        press_holdon: float | None = None,
        press_count: int = 1,
        press_interval: float = 0.3,
        require_buff_codes: list[str] = [],
        generate_buff_codes: list[str] = [],
    ):
        super().__init__(code=code, name=name)
        self.key = key
        self.cooldown = cooldown
        self.max_range = max_range
        self.time_consumption = time_consumption
        self.press_holdon = press_holdon
        self.press_count = press_count
        self.press_interval = press_interval
        self.require_buff_codes = require_buff_codes
        self.generate_buff_codes = generate_buff_codes
