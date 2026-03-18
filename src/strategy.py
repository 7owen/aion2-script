from abc import ABC, abstractmethod
from enum import Enum

from bot_config import BotConfig
from game_context import BotState


class CombatState(Enum):
    """战斗模式状态枚举"""

    IDLE = "idle"
    FIGHT = "fight"
    EXTRACT = "extract"
    DEATH = "death"


class StrategyAction(Enum):
    BUFF = "buff"
    SEARCH = "search"
    FIGHT = "fight"
    LOOT = "loot"
    ROTATE_VIEW = "rotate_view"
    EXTRACT_EQUIPMENT = "extract_equipment"
    RESURRECT_CHARACTER = "resurrect_character"
    NONE = "none"


class BaseStrategy(ABC):
    def __init__(self, state: BotState, config: BotConfig):
        self.state = state
        self.config = config

    @abstractmethod
    def next_actions(self) -> tuple[StrategyAction, ...]:
        pass

    @abstractmethod
    def get_state_str(self) -> str:
        pass

    @abstractmethod
    def set_idle_state(self) -> None:
        pass


class CombatStrategy(BaseStrategy):
    def __init__(self, state: BotState, config: BotConfig):
        super().__init__(state, config)
        self.state_name = CombatState.IDLE
        self.cur_try_combat_count = 0

    def next_actions(self) -> tuple[StrategyAction, ...]:
        if self.state_name == CombatState.IDLE:
            if self.state.resurrection_box:
                self.state_name = CombatState.DEATH
                return (StrategyAction.RESURRECT_CHARACTER,)

            if self.state.has_target:
                self.state_name = CombatState.FIGHT
                return (StrategyAction.FIGHT,)

            if self.state.need_extract():
                self.state_name = CombatState.EXTRACT
                return (StrategyAction.BUFF, StrategyAction.EXTRACT_EQUIPMENT)

            if self.cur_try_combat_count < self.config.runtime.max_try_combat_count:
                self.cur_try_combat_count += 1
                return (StrategyAction.BUFF, StrategyAction.SEARCH)

            self.cur_try_combat_count = 0
            return (StrategyAction.BUFF, StrategyAction.ROTATE_VIEW)

        if self.state_name == CombatState.FIGHT:
            if self.state.has_target:
                return (StrategyAction.FIGHT,)
            self.set_idle_state()
            return (StrategyAction.LOOT,)

        if self.state_name == CombatState.EXTRACT:
            self.set_idle_state()
            return (StrategyAction.EXTRACT_EQUIPMENT,)

        if self.state_name == CombatState.DEATH:
            self.set_idle_state()
            return (StrategyAction.RESURRECT_CHARACTER,)

        return (StrategyAction.NONE,)

    def set_idle_state(self) -> None:
        self.state_name = CombatState.IDLE
        self.cur_try_combat_count = 0

    def get_state_str(self) -> str:
        return {
            CombatState.IDLE: "🔍 寻找目标",
            CombatState.FIGHT: "⚔️ 战斗中",
            CombatState.EXTRACT: "🧪 提取中",
            CombatState.DEATH: "💀 死亡",
        }.get(self.state_name, str(self.state_name))


class MiningState(Enum):
    """采矿模式状态枚举"""

    FINDING_ORE = "finding_ore"
    MINING = "mining"
    DEFENDING = "defending"
    DEATH = "death"


class MiningStrategy(BaseStrategy):
    """后续扩展的采矿策略示例"""

    def __init__(self, state: BotState, config: BotConfig):
        super().__init__(state, config)
        self.state_name = MiningState.FINDING_ORE

    def next_actions(self) -> tuple[StrategyAction, ...]:
        if self.state.resurrection_box:
            self.state_name = MiningState.DEATH

        if self.state_name == MiningState.DEFENDING and self.state.has_target:
            return (StrategyAction.FIGHT,)

        if self.state_name == MiningState.DEATH:
            self.set_idle_state()
            return (StrategyAction.RESURRECT_CHARACTER,)

        return (StrategyAction.NONE,)

    def set_idle_state(self) -> None:
        self.state_name = MiningState.FINDING_ORE

    def get_state_str(self) -> str:
        return {
            MiningState.FINDING_ORE: "🔍 寻找矿石",
            MiningState.MINING: "⛏️ 采矿中",
            MiningState.DEFENDING: "⚔️ 采矿反击中",
            MiningState.DEATH: "💀 死亡",
        }.get(self.state_name, str(self.state_name))
