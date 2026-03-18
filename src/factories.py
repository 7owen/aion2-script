from bot_config import BotConfig, RoleType, StrategyType
from game_context import BotState
from player_actions import PlayerActions
from role import Role
from role_bowstar import RoleBowStar
from role_swordstar import RoleSwordStar
from skill_factory import SkillFactory
from strategy import BaseStrategy, CombatStrategy, MiningStrategy


def create_role(
    config: BotConfig,
    player_action: PlayerActions,
    skill_factory: SkillFactory,
    state: BotState,
) -> Role:
    if config.mode.role_type == RoleType.SWORDSTAR:
        return RoleSwordStar(config.role, player_action, skill_factory, state)

    if config.mode.role_type == RoleType.BOWSTAR:
        return RoleBowStar(config.role, player_action, skill_factory, state)

    raise ValueError(f"不支持的角色类型: {config.mode.role_type}")


def create_strategy(config: BotConfig, state: BotState) -> BaseStrategy:
    if config.mode.strategy_type == StrategyType.COMBAT:
        return CombatStrategy(state, config)

    if config.mode.strategy_type == StrategyType.MINING:
        return MiningStrategy(state, config)

    raise ValueError(f"不支持的策略类型: {config.mode.strategy_type}")
