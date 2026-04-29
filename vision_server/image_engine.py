import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from bot_config import OcrRegionConfig, Rect, TemplateMatchConfig, config
from ocr_reader import OcrReaderWrapper

Box = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class PerceptionSnapshot:
    captured_at: float = field(default_factory=time.time)
    health: float | None = None
    mental: float | None = None
    target_box: Box | None = None
    target_distance: int = -1
    resurrection_box: Box | None = None
    active_buff_codes: frozenset[str] = field(default_factory=frozenset)
    errors: tuple[str, ...] = ()

    @property
    def has_target(self) -> bool:
        return self.target_box is not None


BUFF_BAOJI = "baoji"
BUFF_GEDANG = "gedang"


@dataclass(frozen=True, slots=True)
class OcrParseSpec:
    allowlist: str
    pattern: re.Pattern[str]
    window_name: str
    show_window: bool = False


@dataclass(frozen=True, slots=True)
class OcrRegionSpec:
    rect: Rect
    parse_spec: OcrParseSpec


@dataclass(frozen=True, slots=True)
class LoadedTemplate:
    path: str
    image: object
    mask: object | None
    tolerance: float
    h: int
    w: int


class ImageEngine:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.target_detection_mode = config.vision.target_detection_mode.lower()
        if self.target_detection_mode not in {"template", "yolo"}:
            raise ValueError(
                f"不支持的目标识别模式: {config.vision.target_detection_mode}"
            )

        self.yolo_model = None
        if self.target_detection_mode == "yolo":
            from yolo_detector import YoloDetector

            self.yolo_model = YoloDetector(
                str(self._resolve_path(config.video.model_path)),
                prefer_mps=config.video.prefer_mps,
            )

        # 禁用 OpenCV OpenCL 加速，并限制线程数为 1。
        # 在运行 CPU 密集型游戏时，限制线程数可以减少核心争抢和上下文切换，从而显著提升响应速度。
        cv2.ocl.setUseOpenCL(False)
        cv2.setNumThreads(1)

        self.ocr_reader = OcrReaderWrapper(config.ocr)
        self.health_spec = self._build_ocr_region_spec(
            config.vision.health_region,
            config.ocr.health_allowlist,
            config.ocr.health_pattern,
        )
        self.mental_spec = self._build_ocr_region_spec(
            config.vision.mental_region,
            config.ocr.health_allowlist,
            config.ocr.health_pattern,
        )
        self.distance_parse_spec = self._build_ocr_parse_spec(
            window_name="Target_Distance",
            allowlist=config.ocr.distance_allowlist,
            pattern=config.ocr.distance_pattern,
            show_window=False,
        )
        self.templates = self._load_templates()

    def _build_ocr_parse_spec(
        self,
        window_name: str,
        allowlist: str,
        pattern: str,
        show_window: bool = False,
    ) -> OcrParseSpec:
        return OcrParseSpec(
            allowlist=allowlist,
            pattern=re.compile(pattern, re.IGNORECASE),
            window_name=window_name,
            show_window=show_window,
        )

    def _build_ocr_region_spec(
        self,
        region_config: OcrRegionConfig,
        allowlist: str,
        pattern: str,
    ) -> OcrRegionSpec:
        return OcrRegionSpec(
            rect=region_config.rect,
            parse_spec=self._build_ocr_parse_spec(
                window_name=region_config.window_name,
                allowlist=allowlist,
                pattern=pattern,
                show_window=region_config.show_window,
            ),
        )

    def _resolve_path(self, path: str) -> Path:
        template_path = Path(path)
        if template_path.is_absolute():
            return template_path
        return (self.project_root / template_path).resolve()

    def _load_template(self, template_config: TemplateMatchConfig) -> LoadedTemplate:
        template_path = self._resolve_path(template_config.path)
        img_template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
        if img_template is None:
            raise FileNotFoundError(f"无法读取模板图片，请检查路径: {template_path}")

        img_mask = None
        if len(img_template.shape) == 3 and img_template.shape[2] == 4:
            img_mask = img_template[:, :, 3]
            img_template = cv2.cvtColor(img_template[:, :, :3], cv2.COLOR_BGR2GRAY)
        elif len(img_template.shape) == 3:
            img_template = cv2.cvtColor(img_template, cv2.COLOR_BGR2GRAY)

        # 回归 CPU 存储模板
        h, w = img_template.shape[:2]
        return LoadedTemplate(
            path=str(template_path),
            image=img_template,
            mask=img_mask,
            tolerance=template_config.tolerance,
            h=h,
            w=w,
        )

    def _load_templates(self) -> dict[str, LoadedTemplate]:
        templates = {
            "resurrection": self._load_template(
                config.vision.resurrection_button_match
            ),
            "liweijian": self._load_template(config.vision.liweijian_icon_match),
            "jiaohuaizhan": self._load_template(config.vision.jiaohuaizhan_icon_match),
        }
        if self.target_detection_mode == "template":
            templates["target"] = self._load_template(
                config.vision.top_target_icon_match
            )
        return templates

    def _crop_image(self, frame, x1, y1, x2, y2):
        """根据输入的坐标裁剪出对应的图像区域用于识别。"""
        if frame is None:
            return None

        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 >= x2 or y1 >= y2:
            return None

        return frame[y1:y2, x1:x2].copy()

    def _extract_text_via_ocr(self, pic, parse_spec: OcrParseSpec):
        """统一 OCR 处理流程。"""
        t_pre_start = time.perf_counter()
        processed_pic = self._preprocess_image_for_ocr(pic)
        t_pre_end = time.perf_counter()
        if processed_pic is None:
            return None, f">>> {parse_spec.window_name} OCR 处理失败，预处理图片失败"

        if parse_spec.show_window:
            cv2.imshow(parse_spec.window_name, processed_pic)
            cv2.waitKey(1)

        try:
            t_ocr_start = time.perf_counter()
            ocr_result = self.ocr_reader.readtext(
                processed_pic,
                allowlist=parse_spec.allowlist,
            )
            t_ocr_end = time.perf_counter()
            print(
                f"[PERF] {parse_spec.window_name}: Pre={(t_pre_end - t_pre_start) * 1000:.1f}ms, OCR={(t_ocr_end - t_ocr_start) * 1000:.1f}ms"
            )
            text_combined = "".join(str(t) for t in ocr_result).replace(",", "")

            match = parse_spec.pattern.search(text_combined)
            if match:
                return match.groups(), None
            return (
                None,
                f">>> {parse_spec.window_name} OCR 提取失败，原文: '{text_combined}'",
            )
        except Exception as exc:
            return None, f">>> {parse_spec.window_name} OCR 处理出错: {exc}"

    def _preprocess_image_for_ocr(self, pic, fx=3, fy=3):
        if pic is None or pic.size == 0:
            return None

        # 1. 先转灰度（此时图最小，处理最快）
        gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)

        # 2. 在单通道上做反转
        inverted = cv2.bitwise_not(gray)

        # 3. 在单通道上做放大（插值计算量减少 2/3）
        zoomed = cv2.resize(
            inverted, None, fx=fx, fy=fy, interpolation=cv2.INTER_CUBIC
        )

        # 4. 最后转回 BGR 格式以兼容 RapidOCR 接口要求
        return cv2.cvtColor(zoomed, cv2.COLOR_GRAY2BGR)

    def _perfect_match_and_locate(
        self,
        template: LoadedTemplate,
        target_frame,
        debug: bool = False,
    ):
        if target_frame is None or target_frame.size == 0:
            return None

        # 回归 CPU 匹配
        if len(target_frame.shape) == 3:
            img_target = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
        else:
            img_target = target_frame

        ih, iw = target_frame.shape[:2]
        return self._pixel_perfect_match_and_locate(
            template.image,
            img_target,
            template.tolerance,
            template.h,
            template.w,
            ih,
            iw,
            template.mask,
            debug,
        )

    def _pixel_perfect_match_and_locate(
        self,
        img_template,
        img_target,
        tolerance,
        th,
        tw,
        ih,
        iw,
        img_mask=None,
        debug=False,
    ):
        """
        使用像素级完全匹配定位模板位置。
        - tolerance=0.0: 仅接受完全一致的像素块
        - tolerance>0.0: 允许少量像素差异，取值建议在 0.0 到 1.0 之间
        - 使用 TM_SQDIFF_NORMED，误差越接近 0 越好
        返回: (x1, y1, x2, y2) 或 None
        """

        if th > ih or tw > iw:
            if debug:
                print("匹配失败 - 模板尺寸大于目标图。")
            return None

        t0 = time.perf_counter()
        if img_mask is not None:
            result = cv2.matchTemplate(
                img_target,
                img_template,
                cv2.TM_SQDIFF_NORMED,
                mask=img_mask,
            )
        else:
            result = cv2.matchTemplate(img_target, img_template, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)
        dt = (time.perf_counter() - t0) * 1000
        if dt > 1.0:  # 只有大于1ms的才打印，证明在大图或复杂匹配下的开销
            # print(f"[PERF] matchTemplate took: {dt:.2f}ms")
            pass
        if debug:
            print(f"像素匹配最小归一化误差: {min_val:.8f}")

        if min_val <= tolerance:
            x_min, y_min = min_loc
            return x_min, y_min, x_min + tw, y_min + th
        return None

    @staticmethod
    def _translate_box(box: Box, dx: int, dy: int) -> Box:
        x1, y1, x2, y2 = box
        return x1 + dx, y1 + dy, x2 + dx, y2 + dy

    def _get_target_search_rect(self) -> Rect:
        return Rect(
            config.vision.frame_crop_x_offset,
            config.vision.frame_crop_y_offset,
            config.vision.frame_crop_x_offset + config.vision.frame_crop_width,
            config.vision.frame_crop_y_offset + config.vision.frame_crop_height,
        )

    def _detect_target_box_with_yolo(self, frame):
        if self.yolo_model is None:
            return None

        return self.yolo_model.detect(
            frame,
            imgsz=config.vision.yolo_imgsz,
            conf=config.vision.yolo_conf,
            tag="Top_Target_Tag",
        )

    def _detect_target_box(self, frame):
        if self.target_detection_mode == "yolo":
            return self._detect_target_box_with_yolo(frame)
        return self._perfect_match_and_locate(self.templates["target"], frame)

    def _read_region_groups(self, frame, spec: OcrRegionSpec):
        rect = spec.rect
        pic = self._crop_image(frame, rect.x1, rect.y1, rect.x2, rect.y2)
        return self._extract_text_via_ocr(pic, spec.parse_spec)

    def _read_ratio_from_region(self, frame, spec: OcrRegionSpec):
        result, err_msg = self._read_region_groups(frame, spec)
        if result and len(result) >= 2:
            max_value = int(result[1])
            if max_value != 0:
                return int(result[0]) / max_value, None
            return -1, f">>> {spec.parse_spec.window_name} OCR 提取失败，分母为 0"
        return -1, err_msg

    def analyze(
        self,
        frame,
        check_vitals: bool = True,
        check_buffs: bool = True,
        check_resurrection: bool = True,
        check_target_distance: bool = True,
    ) -> PerceptionSnapshot:
        now = time.time()
        errors: list[str] = []
        active_buffs: set[str] = set()
        target_box = self.get_target_box(frame)
        target_distance = -1
        resurrection_box = None
        health = None
        mental = None

        if check_buffs:
            if self.is_liweijian_valid(frame):
                active_buffs.add(BUFF_BAOJI)
            if self.is_jiaohuaizhan_valid(frame):
                active_buffs.add(BUFF_GEDANG)

        if check_vitals:
            health, health_error = self.get_health_value(frame)
            if health_error is not None:
                errors.append(health_error)
                health = None
            # mental, mental_error = self.get_mental_value(frame)
            # if mental_error is not None:
            # errors.append(mental_error)
            # mental = None

        if target_box:
            if check_target_distance:
                target_distance, target_distance_error = (
                    self.get_distance_from_target_box(
                        frame,
                        target_box,
                    )
                )
                if target_distance_error is not None:
                    errors.append(target_distance_error)
                    target_distance = -1
        else:
            if check_resurrection:
                resurrection_box = self.get_resurrection_box(frame)

        return PerceptionSnapshot(
            captured_at=now,
            health=health,
            mental=mental,
            target_box=target_box,
            target_distance=target_distance,
            resurrection_box=resurrection_box,
            active_buff_codes=frozenset(active_buffs),
            errors=tuple(errors),
        )

    def get_health_value(self, frame):
        """识别屏幕特定区域的生命值 OCR 文本并转化为百分比。"""
        return self._read_ratio_from_region(frame, self.health_spec)

    def get_mental_value(self, frame):
        """识别屏幕特定区域的活力值 OCR 文本并转化为百分比。"""
        return self._read_ratio_from_region(frame, self.mental_spec)

    def get_target_box(self, frame):
        search_rect = self._get_target_search_rect()
        top_image = self._crop_image(
            frame,
            search_rect.x1,
            search_rect.y1,
            search_rect.x2,
            search_rect.y2,
        )
        if top_image is None:
            return None
        target_box = self._detect_target_box(top_image)
        if target_box is None:
            return None
        return self._translate_box(target_box, search_rect.x1, search_rect.y1)

    def _get_distance_box(self, target_box: Box) -> Box:
        t_x1, t_y1, _, _ = target_box
        distance_box = config.vision.target_distance_box
        return (
            t_x1 + distance_box.x1_offset,
            t_y1 + distance_box.y1_offset,
            t_x1 + distance_box.x2_offset,
            t_y1 + distance_box.y2_offset,
        )

    def get_distance_from_target_box(self, frame, target_box):
        distance_box = self._get_distance_box(target_box)
        x1, y1, x2, y2 = distance_box
        pic = self._crop_image(frame, x1, y1, x2, y2)
        result, err_msg = self._extract_text_via_ocr(pic, self.distance_parse_spec)
        if result:
            return int(result[0]), None
        return -1, err_msg

    def get_resurrection_box(self, frame):
        """优化：不进行全屏搜索，只在屏幕中间 1/3 高度区域寻找复活按钮以节省 CPU。"""
        h, w = frame.shape[:2]
        # 高度取中间 1/3 (33% 到 66%)，宽度不变
        y1 = h // 3
        y2 = 2 * h // 3

        crop = self._crop_image(frame, 0, y1, w, y2)
        if crop is None:
            return None

        res = self._perfect_match_and_locate(self.templates["resurrection"], crop)
        if res:
            # 匹配结果是相对于裁剪区域的，需要将 y 坐标平移回全屏坐标系
            return self._translate_box(res, 0, y1)
        return None

    def is_liweijian_valid(self, frame):
        rect = config.vision.liweijian_region
        skill_status_frame = self._crop_image(frame, rect.x1, rect.y1, rect.x2, rect.y2)
        ret = self._perfect_match_and_locate(
            self.templates["liweijian"],
            skill_status_frame,
        )
        return ret is not None

    def is_jiaohuaizhan_valid(self, frame):
        rect = config.vision.liweijian_region
        skill_status_frame = self._crop_image(frame, rect.x1, rect.y1, rect.x2, rect.y2)
        ret = self._perfect_match_and_locate(
            self.templates["jiaohuaizhan"],
            skill_status_frame,
        )
        return ret is not None

    def get_ocr_debug_frame(self, frame) -> np.ndarray:
        """获取所有 OCR 区域预处理后的拼接图像，用于调试。"""
        # 定义需要显示的 OCR 任务区域
        regions = [
            ("Health", self.health_spec),
            ("Mental", self.mental_spec),
        ]

        # 如果有目标，增加距离显示
        target_box = self.get_target_box(frame)
        if target_box:
            dist_rect = self._get_distance_box(target_box)
            dist_spec = OcrRegionSpec(
                rect=Rect(*dist_rect), parse_spec=self.distance_parse_spec
            )
            regions.append(("Distance", dist_spec))

        processed_pics = []
        for name, spec in regions:
            rect = spec.rect
            # 裁剪原始区域
            pic = self._crop_image(frame, rect.x1, rect.y1, rect.x2, rect.y2)
            # 运行你在 _preprocess_image_for_ocr 中定义的反转+放大逻辑
            processed = self._preprocess_image_for_ocr(pic)

            # 在图像上方绘制标签以便识别
            h, w = processed.shape[:2]
            # 创建一个稍微大一点的画布来放文字
            canvas = np.zeros((h + 30, w, 3), dtype=np.uint8)
            cv2.putText(
                canvas,
                name,
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
            canvas[30:, :] = processed
            processed_pics.append(canvas)

        if not processed_pics:
            # 如果没有任何区域，返回一张黑图
            return np.zeros((100, 100, 3), dtype=np.uint8)

        # 将所有图片垂直拼接在一起
        # 统一宽度以方便拼接
        max_w = max(p.shape[1] for p in processed_pics)
        resized_pics = []
        for p in processed_pics:
            if p.shape[1] < max_w:
                # 填充黑色背景
                padded = np.zeros((p.shape[0], max_w, 3), dtype=np.uint8)
                padded[:, : p.shape[1]] = p
                resized_pics.append(padded)
            else:
                resized_pics.append(p)

        return np.vstack(resized_pics)
