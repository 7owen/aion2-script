import warnings

import cv2
import torch
from ultralytics.engine.results import Results
from ultralytics.models.yolo import YOLO

from bot_config import VideoConfig

# 屏蔽掉这个特定的 MPS 警告
warnings.filterwarnings("ignore", message=".*pin_memory.*")


class VideoCapture:
    def __init__(self, config: VideoConfig | None = None) -> None:
        self.config = config or VideoConfig()
        self.model = self.create_model(
            self.config.model_path,
            prefer_mps=self.config.prefer_mps,
        )
        self.cap = self.create_cap(
            camera_index=self.config.camera_index,
            frame_width=self.config.frame_width,
            frame_height=self.config.frame_height,
        )
        self.results: list[Results] = []
        self.current_frame = None

    def create_model(self, model_path: str, prefer_mps: bool = True):
        try:
            model = YOLO(model_path)

            # 检查是否可以使用 Apple M 系列芯片的 GPU (MPS)
            if prefer_mps and torch.backends.mps.is_available():
                model.to("mps")
            else:
                print("未检测到 MPS 或已禁用，将使用 CPU 运行。")

            return model
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise e

    def create_cap(self, camera_index: int, frame_width: int, frame_height: int):
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        if not cap.isOpened():
            print("错误: 无法打开摄像头。请检查连接或权限。")
            raise Exception("摄像头打开失败")
        return cap

    def capture_pic(self, frame, x1, y1, x2, y2):
        """根据输入的 座标 裁剪出对应的图像区域用于 OCR"""
        if frame is None:
            return None

        # 确保坐标为整数，避免切片时浮点数报错
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        # 边界检查，防止切片越界
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        # 返回裁剪后的图像区域 (ROI)
        return frame[y1:y2, x1:x2].copy()

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def predict(self, frame, imgsz=256, conf=0.2):
        return self.model.predict(frame, imgsz=imgsz, verbose=False, conf=conf)

    def show_annotated_frame(self, results):
        # 可视化
        for result in results:
            # plot() 方法会在图像上绘制检测到的边界框和标签
            # 返回的是一个 BGR 格式的 numpy 数组，可以直接用 OpenCV 显示
            annotated_frame = result.plot()

            # 获取图像中心点坐标 (用于绘制准星)
            h, w = annotated_frame.shape[:2]
            center = (w // 2, h // 2)

            cv2.drawMarker(
                annotated_frame,
                center,
                (0, 255, 0),
                markerType=cv2.MARKER_CROSS,
                thickness=2,
            )
            # 直接显示原始大小图像，移除强制缩放
            cv2.imshow("PID Debug", annotated_frame)

        cv2.waitKey(1)

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
