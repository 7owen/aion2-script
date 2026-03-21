from abc import ABC, abstractmethod
from enum import Enum

from bot_config import config
from game_context import BotState


class CombatState(Enum):
    """战斗模式状态枚举"""

    IDLE = "idle"
    FIGHT = "fight"


class StrategyAction(Enum):
    BUFF = "buff"
    SEARCH = "search"
    FIRST_FIGHT = "first_fight"
    LOOP_FIGHT = "loop_fight"
    LOOT = "loot"
    ROTATE_VIEW = "rotate_view"
    EXTRACT_EQUIPMENT = "extract_equipment"
    RESURRECT_CHARACTER = "resurrect_character"
    NONE = "none"


class BaseStrategy(ABC):
    def __init__(self, state: BotState):
        self.state = state

    @abstractmethod
    def next_actions(self) -> tuple[StrategyAction, ...]:
        pass

    @abstractmethod
    def set_idle_state(self) -> None:
        pass

    @abstractmethod
    def get_status_info(self) -> str:
        pass


class CombatStrategy(BaseStrategy):
    def __init__(self, state: BotState):
        super().__init__(state)
        self.state_name = CombatState.IDLE
        self.cur_try_combat_count = 0

    def next_actions(self) -> tuple[StrategyAction, ...]:
        if self.state_name == CombatState.IDLE:
            if self.state.resurrection_btn:
                return (StrategyAction.RESURRECT_CHARACTER,)

            if self.state.has_target:
                self.state_name = CombatState.FIGHT
                return (StrategyAction.FIRST_FIGHT,)

            if self.state.need_extract():
                return (StrategyAction.BUFF, StrategyAction.EXTRACT_EQUIPMENT)

            if self.cur_try_combat_count < config.runtime.max_try_combat_count:
                self.cur_try_combat_count += 1
                return (StrategyAction.BUFF, StrategyAction.SEARCH)

            self.cur_try_combat_count = 0
            return (StrategyAction.BUFF, StrategyAction.ROTATE_VIEW)

        if self.state_name == CombatState.FIGHT:
            if self.state.has_target:
                return (StrategyAction.LOOP_FIGHT,)
            self.set_idle_state()
            return (StrategyAction.LOOT,)

        return (StrategyAction.NONE,)

    def set_idle_state(self) -> None:
        self.state_name = CombatState.IDLE
        self.cur_try_combat_count = 0

    def get_status_info(self) -> str:
        return f"{self.state_name} 状态"


class MiningState(Enum):
    """采矿模式状态枚举"""

    FINDING_ORE = "finding_ore"
    MINING = "mining"
    DEFENDING = "defending"
    DEATH = "death"


class MiningStrategy(BaseStrategy):
    """后续扩展的采矿策略示例"""

    def __init__(self, state: BotState):
        super().__init__(state)
        self.state_name = MiningState.FINDING_ORE

    def next_actions(self) -> tuple[StrategyAction, ...]:
        if self.state.resurrection_btn:
            self.state_name = MiningState.DEATH

        if self.state_name == MiningState.DEFENDING and self.state.has_target:
            return (StrategyAction.LOOP_FIGHT,)

        if self.state_name == MiningState.DEATH:
            self.set_idle_state()
            return (StrategyAction.RESURRECT_CHARACTER,)

        return (StrategyAction.NONE,)

    def set_idle_state(self) -> None:
        self.state_name = MiningState.FINDING_ORE

    def get_status_info(self) -> str:
        return f"{self.state_name} 状态"
