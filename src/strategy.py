import time
from abc import ABC, abstractmethod
from enum import Enum

from bot_config import BotConfig
from game_context import GameContext
from player_controller import PlayerController
from role import Role


class CombatState(Enum):
    """战斗模式状态枚举"""

    IDLE = "idle"  # 空闲状态，用于寻怪或执行日常操作
    FIGHT = "fight"  # 战斗状态，正在攻击目标
    EXTRACT = "extract"  # 采集状态，正在进行资源提取
    DEATH = "death"


class BaseStrategy(ABC):
    def __init__(
        self,
        context: GameContext,
        player_ctrl: PlayerController,
        role: Role,
        config: BotConfig,
    ):
        self.context = context
        self.player_ctrl = player_ctrl
        self.role = role
        self.config = config

    @abstractmethod
    def action(self):
        pass

    @abstractmethod
    def get_state_str(self) -> str:
        pass

    @abstractmethod
    def set_idle_state(self):
        pass


class CombatStrategy(BaseStrategy):
    def __init__(
        self,
        context: GameContext,
        player_ctrl: PlayerController,
        role: Role,
        config: BotConfig,
    ):
        super().__init__(context, player_ctrl, role, config)
        self.state = CombatState.IDLE
        self.cur_try_combat_count = 0

    def action(self):
        """状态机核心逻辑：根据当前状态执行相应动作。"""
        if self.state == CombatState.IDLE:
            self.role.buff()
            if self.context.resurrection_box:
                self.state = CombatState.DEATH
            elif self.context.has_target:
                self.state = CombatState.FIGHT
            elif self.context.need_extract():
                self.state = CombatState.EXTRACT
            else:
                # 尝试搜寻，若次数耗尽则旋转视角
                if self.cur_try_combat_count < self.config.runtime.max_try_combat_count:
                    self.cur_try_combat_count += 1
                    self.role.search()
                    time.sleep(0.5)
                else:
                    self.cur_try_combat_count = 0
                    self.player_ctrl.rotate_view()
        elif self.state == CombatState.FIGHT:
            if self.context.has_target:
                self.role.fight()
            else:
                self.player_ctrl.loot()
                self.set_idle_state()
        elif self.state == CombatState.EXTRACT:
            self.player_ctrl.extraction()
            self.set_idle_state()
        elif self.state == CombatState.DEATH:
            self.player_ctrl.resurrect(self.context.resurrection_box)
            self.context.resurrection_box = None
            self.set_idle_state()

    def set_idle_state(self):
        self.state = CombatState.IDLE
        self.cur_try_combat_count = 0

    def get_state_str(self) -> str:
        return {
            CombatState.IDLE: "🔍 寻找目标",
            CombatState.FIGHT: "⚔️ 战斗中",
            CombatState.EXTRACT: "🧪 提取中",
            CombatState.DEATH: "💀 死亡",
        }.get(self.state, str(self.state))


class MiningState(Enum):
    """采矿模式状态枚举"""

    FINDING_ORE = "finding_ore"  # 寻找矿石
    MINING = "mining"  # 采矿中
    DEFENDING = "defending"  # 采矿被攻击，进行反击
    DEATH = "death"


class MiningStrategy(BaseStrategy):
    """后续扩展的采矿策略示例"""

    def __init__(
        self,
        context: GameContext,
        player_ctrl: PlayerController,
        role: Role,
        config: BotConfig,
    ):
        super().__init__(context, player_ctrl, role, config)
        self.state = MiningState.FINDING_ORE

    def action(self):
        # 遇到复活按钮直接转为死亡状态
        if self.context.resurrection_box:
            self.state = MiningState.DEATH

        if self.state == MiningState.FINDING_ORE:
            # TODO: 寻找矿石逻辑
            pass
        elif self.state == MiningState.MINING:
            # TODO: 采矿进度条识别与交互逻辑
            pass
        elif self.state == MiningState.DEFENDING:
            # TODO: 采矿时被怪打了，调用战斗逻辑还击
            if self.context.has_target:
                self.role.fight()
            else:
                self.set_idle_state()
        elif self.state == MiningState.DEATH:
            self.player_ctrl.resurrect(self.context.resurrection_box)
            self.context.resurrection_box = None
            self.set_idle_state()

    def set_idle_state(self):
        self.state = MiningState.FINDING_ORE

    def get_state_str(self) -> str:
        return {
            MiningState.FINDING_ORE: "🔍 寻找矿石",
            MiningState.MINING: "⛏️ 采矿中",
            MiningState.DEFENDING: "⚔️ 采矿反击中",
            MiningState.DEATH: "💀 死亡",
        }.get(self.state, str(self.state))
