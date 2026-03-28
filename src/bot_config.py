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
class Rect:
    """表示屏幕上的矩形区域 [x1, y1, x2, y2]。"""

    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(frozen=True)
class RelativeRect:
    """表示相对于锚点坐标的矩形偏移 [x1, y1, x2, y2]。"""

    x1_offset: int
    y1_offset: int
    x2_offset: int
    y2_offset: int


@dataclass(frozen=True)
class OcrRegionConfig:
    """描述一个固定区域上的 OCR 识别规格。"""

    rect: Rect
    window_name: str
    show_window: bool = False


@dataclass(frozen=True)
class TemplateMatchConfig:
    """描述一个模板匹配资源及其容差。"""

    path: str
    tolerance: float = 0.1


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
            RoleType.BOWSTAR,
            # RoleType.SWORDSTAR,
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
class VisionConfig:
    """计算机视觉与图像处理配置。"""

    # 截图裁剪区域（通常用于 YOLO 推理加速）
    frame_crop_x_offset: int = 720
    frame_crop_y_offset: int = 0
    frame_crop_width: int = 480
    frame_crop_height: int = 150

    # YOLO 模型参数
    yolo_imgsz: int = 256
    yolo_conf: float = 0.2
    target_detection_mode: str = "template"

    # UI 识别矩形区域
    health_region: OcrRegionConfig = field(
        default_factory=lambda: OcrRegionConfig(
            rect=Rect(791, 959, 911, 973),
            window_name="Health_Value",
        )
    )
    mental_region: OcrRegionConfig = field(
        default_factory=lambda: OcrRegionConfig(
            rect=Rect(1010, 959, 1130, 973),
            window_name="Mental_Value",
        )
    )

    # 目标识别和模板匹配资源
    top_target_icon_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path="src/images/top-target-right-icon.png",
            tolerance=0.1,
        )
    )
    resurrection_button_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path="src/images/resurrection-btn.png",
            tolerance=0.1,
        )
    )
    liweijian_icon_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path="src/images/baoji_icon.png",
            tolerance=0.1,
        )
    )

    jiaohuaizhan_icon_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path="src/images/jiaohuaizhan_icon.png",
            tolerance=0.1,
        )
    )

    # 技能状态与目标距离估算区域
    liweijian_region: Rect = field(default_factory=lambda: Rect(1257, 466, 1329, 538))
    target_distance_box: RelativeRect = field(
        default_factory=lambda: RelativeRect(
            x1_offset=-50,
            y1_offset=-20,
            x2_offset=-12,
            y2_offset=0,
        )
    )


@dataclass(frozen=True)
class OcrConfig:
    """文字识别 (OCR) 相关配置。"""

    languages: tuple[str, ...] = ("en",)  # OCR 使用语言
    use_gpu: bool = True  # 是否使用 GPU 加速识别

    # 血量 OCR 过滤规则
    health_allowlist: str = "0123456789,/"
    health_pattern: str = r"(\d+)/(\d+)"

    # 距离 OCR 过滤规则
    distance_allowlist: str = "0123456789,M"
    distance_pattern: str = r"(\d+)M"


@dataclass(frozen=True)
class VideoConfig:
    """视频流与模型加载配置。"""

    model_path: str = "src/aion2.pt"  # YOLO 模型权重路径
    camera_index: int = 0  # 采集源索引（通常是物理摄像头或虚拟视频采集卡）
    frame_width: int = 1920  # 视频采集宽度
    frame_height: int = 1080  # 视频采集高度
    prefer_mps: bool = True  # 在 macOS 上是否优先使用 MPS (Metal Performance Shaders)


@dataclass(frozen=True)
class KmboxConfig:
    """Kmbox B+ 网络版硬件控制配置。"""

    ip: str = "192.168.2.188"
    port: int = 8888
    mac: str = "0B50E466"
    monitor_port: int = 12345  # 用于键盘鼠标事件回显的监控端口
    screen_width: int = 1920  # 目标机屏幕宽度
    screen_height: int = 1080  # 目标机屏幕高度
    auto_mouse_reset: bool = True  # 初始化时是否自动校准鼠标位置

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
            auto_mouse_reset=os.getenv("KMBOX_AUTO_MOUSE_RESET", "1")
            not in {"0", "false", "False"},
        )


@dataclass(frozen=True)
class BotConfig:
    """机器人完整配置汇总。"""

    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    mode: ModeConfig = field(default_factory=ModeConfig)
    role: RoleConfig = field(default_factory=RoleConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    kmbox: KmboxConfig = field(default_factory=KmboxConfig.from_env)


config = BotConfig()
