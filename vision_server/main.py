import asyncio
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from image_engine import ImageEngine
from pydantic import BaseModel
from video_capture import VideoCapture

# 共享状态与锁
_camera_lock = threading.Lock()
_engine: Optional[ImageEngine] = None
_video_capture: Optional[VideoCapture] = None
_running = True


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
    """后台独立线程：仅执行硬件级别的帧抓取(grab)，清空缓冲区且不耗费CPU解码"""
    global _running
    while _running:
        if _video_capture:
            with _camera_lock:
                _video_capture.grab()
            # 增加休眠时间以匹配 30FPS 采集，显著降低 CPU 占用
            time.sleep(0.03)
        else:
            time.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _video_capture, _running
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

    _running = False
    if _video_capture:
        _video_capture.release()
    print("Vision Server shut down.")


app = FastAPI(title="Vision Perception Server", lifespan=lifespan)


@app.get("/api/perception", response_model=PerceptionResponse)
def get_perception(check_vitals: bool = True, check_resurrection: bool = True):
    """
    当客户端（Bot）请求时，拿出最新的一帧进行推理分析。
    """
    global _engine, _video_capture

    if _engine is None or _video_capture is None:
        raise HTTPException(status_code=503, detail="Services not fully initialized")

    with _camera_lock:
        frame_to_process = _video_capture.retrieve_frame()

    if frame_to_process is None:
        raise HTTPException(status_code=503, detail="No video frame available")

    # 执行繁重的推理任务
    snapshot = _engine.analyze(
        frame_to_process,
        check_vitals=check_vitals,
        check_resurrection=check_resurrection,
    )

    # 将感知结果序列化为 API 响应
    resp = PerceptionResponse(
        captured_at=snapshot.captured_at,
        health=snapshot.health,
        mental=snapshot.mental,
        target_distance=snapshot.target_distance,
        has_target=snapshot.has_target,
        resurrection_btn_visible=snapshot.resurrection_box is not None,
        active_buff_codes=list(snapshot.active_buff_codes),
        errors=list(snapshot.errors),
    )
    # print(f">>> API Response: {resp.model_dump_json()}")
    return resp


async def generate_frames():
    global _running

    while _running:
        if _video_capture is None:
            await asyncio.sleep(0.1)
            continue

        with _camera_lock:
            frame = _video_capture.retrieve_frame()

        if frame is None:
            await asyncio.sleep(0.1)
            continue

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )

        # 限制最高下发帧率（约 30 FPS）
        await asyncio.sleep(0.03)


@app.get("/api/stream")
def video_stream():
    """
    提供实时的 MJPEG 视频流，可以在浏览器中直接查看。
    """
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
