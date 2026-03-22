import re
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import easyocr
import torch
from ultralytics.models.yolo import YOLO

from bot_config import OcrConfig, OcrRegionConfig, Rect, TemplateMatchConfig, config
from game_context import Box, PerceptionSnapshot
from models.skill_data import BUFF_BAOJI, BUFF_GEDANG


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
            self.yolo_model = self._create_yolo_model(
                config.video.model_path,
                prefer_mps=config.video.prefer_mps,
            )

        self.ocr_reader = self._create_ocr_reader(config.ocr)
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
        )
        self.templates = self._load_templates()

    def _create_yolo_model(self, model_path: str, prefer_mps: bool = True):
        try:
            model = YOLO(str(self._resolve_path(model_path)))

            if prefer_mps and torch.backends.mps.is_available():
                model.to("mps")
            else:
                print("未检测到 MPS 或已禁用，将使用 CPU 运行。")

            return model
        except Exception as exc:
            print(f"模型加载失败: {exc}")
            raise

    def _create_ocr_reader(self, ocr_config: OcrConfig):
        """初始化 OCR 引擎。若配置 GPU 加速但初始化失败，则自动回退至 CPU 模式。"""
        try:
            return easyocr.Reader(list(ocr_config.languages), gpu=ocr_config.use_gpu)
        except Exception as exc:
            if ocr_config.use_gpu:
                print(f">>> OCR GPU 初始化失败，降级到 CPU: {exc}")
                return easyocr.Reader(list(ocr_config.languages), gpu=False)
            raise

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

        return LoadedTemplate(
            path=str(template_path),
            image=img_template,
            mask=img_mask,
            tolerance=template_config.tolerance,
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
        processed_pic = self._preprocess_image_for_ocr(pic)
        if processed_pic is None:
            return None, f">>> {parse_spec.window_name} OCR 处理失败，预处理图片失败"

        if parse_spec.show_window:
            cv2.imshow(parse_spec.window_name, processed_pic)
            cv2.waitKey(1)

        try:
            ocr_result = self.ocr_reader.readtext(
                processed_pic,
                detail=0,
                allowlist=parse_spec.allowlist,
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

    def _preprocess_image_for_ocr(self, pic, fx=2, fy=2):
        if pic is None or pic.size == 0:
            return None

        gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        zoomed = cv2.resize(gray, None, fx=fx, fy=fy, interpolation=cv2.INTER_CUBIC)
        return cv2.bitwise_not(zoomed)

    def _perfect_match_and_locate(
        self,
        template: LoadedTemplate,
        target_frame,
        debug: bool = False,
    ):
        if target_frame is None or target_frame.size == 0:
            return None

        if len(target_frame.shape) == 3:
            img_target = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
        else:
            img_target = target_frame

        return self._pixel_perfect_match_and_locate(
            template.image,
            img_target,
            template.tolerance,
            template.mask,
            debug,
        )

    def _pixel_perfect_match_and_locate(
        self,
        img_template,
        img_target,
        tolerance=0.0,
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

        th, tw = img_template.shape[:2]
        ih, iw = img_target.shape[:2]
        if th > ih or tw > iw:
            if debug:
                print("匹配失败 - 模板尺寸大于目标图。")
            return None

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
        if debug:
            print(f"像素匹配最小归一化误差: {min_val:.8f}")

        if min_val <= tolerance:
            x_min, y_min = min_loc
            return x_min, y_min, x_min + tw, y_min + th
        return None

    def _get_tag_box(self, yolo_results, tag):
        if not yolo_results or not yolo_results[0].boxes:
            return None

        names = yolo_results[0].names
        targets = [
            box for box in yolo_results[0].boxes if names[int(box.cls[0])] == tag
        ]
        if not targets:
            return None

        target_box = max(targets, key=lambda box: box.conf[0])
        x1, y1, x2, y2 = map(int, target_box.xyxy[0].tolist())
        return x1, y1, x2, y2

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

        yolo_results = self.yolo_model.predict(
            frame,
            imgsz=config.vision.yolo_imgsz,
            verbose=False,
            conf=config.vision.yolo_conf,
        )
        return self._get_tag_box(yolo_results, "Top_Target_Tag")

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

    def analyze(self, frame, include_vitals: bool = True) -> PerceptionSnapshot:
        now = time.monotonic()
        errors: list[str] = []
        active_buffs: set[str] = set()
        target_box = self.get_target_box(frame)
        target_distance = -1
        resurrection_box = None
        health = None
        mental = None

        if self.is_liweijian_valid(frame):
            active_buffs.add(BUFF_BAOJI)

        if self.is_jiaohuaizhan_valid(frame):
            active_buffs.add(BUFF_GEDANG)

        if include_vitals:
            health, health_error = self.get_health_value(frame)
            mental, mental_error = self.get_mental_value(frame)
            if health_error is not None:
                errors.append(health_error)
                health = None
            if mental_error is not None:
                errors.append(mental_error)
                mental = None

        if target_box:
            target_distance, target_distance_error = self.get_distance_from_target_box(
                frame,
                target_box,
            )
            if target_distance_error is not None:
                errors.append(target_distance_error)
                target_distance = -1
        else:
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
        return self._perfect_match_and_locate(self.templates["resurrection"], frame)

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
            self.templates["jiaohuaizhan"], skill_status_frame
        )
        return ret is not None
