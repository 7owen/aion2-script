import torch
from ultralytics.models.yolo import YOLO


class YoloDetector:
    def __init__(self, model_path: str, prefer_mps: bool = True):
        self.model = self._create_yolo_model(model_path, prefer_mps)

    def _create_yolo_model(self, model_path: str, prefer_mps: bool = True):
        try:
            model = YOLO(str(model_path))

            if prefer_mps and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                model.to("mps")
            elif torch.cuda.is_available():
                model.to("cuda")
                print("检测到 CUDA，将使用 NVIDIA GPU 运行。")
            else:
                print("未检测到 MPS 或 CUDA 或已禁用，将使用 CPU 运行。")

            return model
        except Exception as exc:
            print(f"YOLO 模型加载失败: {exc}")
            raise

    def get_tag_box(self, yolo_results, tag: str):
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

    def detect(self, frame, imgsz, conf, tag="Top_Target_Tag"):
        if self.model is None:
            return None

        yolo_results = self.model.predict(
            frame,
            imgsz=imgsz,
            verbose=False,
            conf=conf,
        )
        return self.get_tag_box(yolo_results, tag)
