import os
from dataclasses import dataclass, field
from enum import Enum


def _env_int(name: str, default: int) -> int:
    """从环境变量读取整数值，如果读取失败或变量不存在则返回默认值。"""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_enum(name: str, enum_type, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return enum_type(value.lower())
    except ValueError:
        return default


@dataclass(frozen=True)
class RuntimeConfig:
    """机器人运行时的控制参数。"""

    max_try_combat_count: int = 3  # 单次战斗尝试的最大次数
    max_ops_per_second: float = 3  # 每秒允许的最大操作频率（防止动作过快被检测）


class RoleType(Enum):
    SWORDSTAR = "swordstar"
    BOWSTAR = "bowstar"


class StrategyType(Enum):
    COMBAT = "combat"
    MINING = "mining"


@dataclass(frozen=True)
class ModeConfig:
    """运行模式选择。"""

    role_type: RoleType = field(
        default_factory=lambda: _env_enum(
            "BOT_ROLE_TYPE",
            RoleType,
            # RoleType.BOWSTAR,
            RoleType.SWORDSTAR,
        )
    )
    strategy_type: StrategyType = field(
        default_factory=lambda: _env_enum(
            "BOT_STRATEGY_TYPE",
            StrategyType,
            StrategyType.COMBAT,
        )
    )


@dataclass(frozen=True)
class RoleConfig:
    """角色相关的行为配置。"""

    extract_interval_seconds: float = 10 * 60  # 自动提取间隔（秒）
    low_health_threshold: float = 0.5  # 血量百分比低于此值时视为低血量状态
    close_distance_threshold: int = 4  # 与目标距离低于此值时视为进入近战范围


@dataclass(frozen=True)
class KmboxConfig:
    """Kmbox B+ 网络版硬件控制配置。"""

    ip: str = "192.168.2.188"
    port: int = 8888
    mac: str = "0B50E466"
    monitor_port: int = 12345  # 用于键盘鼠标事件回显的监控端口
    screen_width: int = 1920  # 目标机屏幕宽度
    screen_height: int = 1080  # 目标机屏幕高度

    @classmethod
    def from_env(cls) -> "KmboxConfig":
        """从系统环境变量加载配置，支持动态调整。"""
        return cls(
            ip=os.getenv("KMBOX_IP", cls.ip),
            port=_env_int("KMBOX_PORT", cls.port),
            mac=os.getenv("KMBOX_MAC", cls.mac),
            monitor_port=_env_int("KMBOX_MONITOR_PORT", cls.monitor_port),
            screen_width=_env_int("KMBOX_SCREEN_WIDTH", cls.screen_width),
            screen_height=_env_int("KMBOX_SCREEN_HEIGHT", cls.screen_height),
        )


@dataclass(frozen=True)
class BotConfig:
    """机器人完整配置汇总。"""

    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    mode: ModeConfig = field(default_factory=ModeConfig)
    role: RoleConfig = field(default_factory=RoleConfig)
    kmbox: KmboxConfig = field(default_factory=KmboxConfig.from_env)


config = BotConfig()
