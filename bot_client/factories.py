from __future__ import annotations

from bot_config import RoleType, StrategyType, config
from game_context import BotState
from km_driver import KmboxDriver
from models.metadata import SkillMetadata
from models.role import Role
from models.role_bowstar import RoleBowStar
from models.role_swordstar import RoleSwordStar
from models.skill import Skill
from player_actions import PlayerActions
from strategy import BaseStrategy, CombatStrategy, MiningStrategy


class SkillFactory:
    def __init__(self, km_driver: KmboxDriver) -> None:
        self.km_driver = km_driver

    def create_skill(self, metadata: SkillMetadata, for_role: Role) -> Skill:
        return Skill(metadata=metadata, km_driver=self.km_driver, for_role=for_role)


def create_role(player_action: PlayerActions, skill_factory: SkillFactory) -> Role:
    if config.mode.role_type == RoleType.SWORDSTAR:
        return RoleSwordStar(player_action, skill_factory)

    if config.mode.role_type == RoleType.BOWSTAR:
        return RoleBowStar(player_action, skill_factory)

    raise ValueError(f"不支持的角色类型: {config.mode.role_type}")


def create_strategy(state: BotState) -> BaseStrategy:
    if config.mode.strategy_type == StrategyType.COMBAT:
        return CombatStrategy(state)

    if config.mode.strategy_type == StrategyType.MINING:
        return MiningStrategy(state)

    raise ValueError(f"不支持的策略类型: {config.mode.strategy_type}")
