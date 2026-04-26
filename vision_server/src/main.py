import asyncio
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from image_engine import ImageEngine
from video_capture import VideoCapture

# 共享变量，用于存储最新的视频帧
_latest_frame = None
_frame_lock = threading.Lock()
_engine: Optional[ImageEngine] = None
_video_capture: Optional[VideoCapture] = None


class PerceptionResponse(BaseModel):
    captured_at: float
    health: float | None
    mental: float | None
    target_distance: int
    has_target: bool
    resurrection_btn_visible: bool
    active_buff_codes: list[str]
    errors: list[str]


def frame_grabber_loop():
    """后台独立线程：不断清空视频采集卡缓冲区，确保获取的帧永远是实时的"""
    global _latest_frame
    while True:
        if _video_capture:
            frame = _video_capture.read_frame()
            if frame is not None:
                with _frame_lock:
                    _latest_frame = frame


        else:
            time.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _video_capture
    print("Initializing Vision Server...")

    # 初始化图像引擎 (YOLO, OCR 等)
    _engine = ImageEngine()

    # 初始化视频捕获
    try:
        _video_capture = VideoCapture()
        print("Camera initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize camera: {e}")

    # 启动后台抓帧线程
    threading.Thread(target=frame_grabber_loop, daemon=True).start()
    print("Frame grabber thread started.")

    yield

    if _video_capture:
        _video_capture.release()
    print("Vision Server shut down.")


app = FastAPI(title="Vision Perception Server", lifespan=lifespan)


@app.get("/api/perception", response_model=PerceptionResponse)
def get_perception(check_vitals: bool = True, check_resurrection: bool = True):
    """
    当客户端（Bot）请求时，拿出最新的一帧进行推理分析。
    """
    global _latest_frame, _engine

    if _engine is None:
        raise HTTPException(status_code=503, detail="Image engine is not initialized")

    with _frame_lock:
        frame_to_process = _latest_frame.copy() if _latest_frame is not None else None

    if frame_to_process is None:
        raise HTTPException(status_code=503, detail="No video frame available")

    # 执行繁重的推理任务
    snapshot = _engine.analyze(
        frame_to_process,
        check_vitals=check_vitals,
        check_resurrection=check_resurrection,
    )

    # 将感知结果序列化为 API 响应
    return PerceptionResponse(
        captured_at=snapshot.captured_at,
        health=snapshot.health,
        mental=snapshot.mental,
        target_distance=snapshot.target_distance,
        has_target=snapshot.has_target,
        resurrection_btn_visible=snapshot.resurrection_box is not None,
        active_buff_codes=list(snapshot.active_buff_codes),
        errors=list(snapshot.errors),
    )


async def generate_frames():
    global _latest_frame
    while True:
        with _frame_lock:
            frame = _latest_frame.copy() if _latest_frame is not None else None

        if frame is None:
            await asyncio.sleep(0.1)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        # 限制下发帧率（约 30 FPS）
        await asyncio.sleep(0.03)


@app.get("/api/stream")
def video_stream():
    """
    提供实时的 MJPEG 视频流，可以在浏览器中直接查看。
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
