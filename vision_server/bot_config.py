import os
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
            path=os.path.join(BASE_DIR, "images", "top-target-right-icon.png"),
            tolerance=0.1,
        )
    )
    resurrection_button_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path=os.path.join(BASE_DIR, "images", "resurrection-btn.png"),
            tolerance=0.1,
        )
    )
    liweijian_icon_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path=os.path.join(BASE_DIR, "images", "baoji_icon.png"),
            tolerance=0.1,
        )
    )

    jiaohuaizhan_icon_match: TemplateMatchConfig = field(
        default_factory=lambda: TemplateMatchConfig(
            path=os.path.join(BASE_DIR, "images", "jiaohuaizhan_icon.png"),
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

    model_path: str = os.path.join(BASE_DIR, "aion2.pt")  # YOLO 模型权重路径
    camera_index: int = 0  # 采集源索引（通常是物理摄像头或虚拟视频采集卡）
    frame_width: int = 1920  # 视频采集宽度
    frame_height: int = 1080  # 视频采集高度
    prefer_mps: bool = True  # 在 macOS 上是否优先使用 MPS (Metal Performance Shaders)


@dataclass(frozen=True)
class BotConfig:
    """机器人完整配置汇总。"""

    vision: VisionConfig = field(default_factory=VisionConfig)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    video: VideoConfig = field(default_factory=VideoConfig)


config = BotConfig()
