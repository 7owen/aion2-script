import sys
import warnings

import cv2

from bot_config import config

# 屏蔽掉这个特定的 MPS 警告
warnings.filterwarnings("ignore", message=".*pin_memory.*")


class VideoCapture:
    def __init__(self) -> None:
        self.config = config.video
        self.cap = self.create_cap(
            camera_index=self.config.camera_index,
            frame_width=self.config.frame_width,
            frame_height=self.config.frame_height,
        )

    def create_cap(self, camera_index: int, frame_width: int, frame_height: int):
        # 在 Windows 上使用 DirectShow 后端可以显著加快 USB 摄像头的初始化速度
        if sys.platform == "win32":
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(camera_index)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        if not cap.isOpened():
            print("错误: 无法打开摄像头。请检查连接或权限。")
            raise Exception("摄像头打开失败")
        return cap

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        self.cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
