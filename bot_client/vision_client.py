import time

import requests

from bot_config import config
from game_context import PerceptionSnapshot


class VisionClient:
    def __init__(self) -> None:
        self._session = requests.Session()

    def check_item_status(self) -> bool:
        """检查背包是否打开"""
        try:
            response = self._session.get(
                f"{config.vision_server.base_url}/api/ui/item_status",
                timeout=1.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("is_open", False)
        except Exception:
            return False

    def fetch_perception_data(
        self, now: float, check_vitals: bool, check_resurrection: bool
    ) -> PerceptionSnapshot:
        """从视觉服务获取感知数据并转换为快照。"""
        response = self._session.get(
            f"{config.vision_server.base_url}/api/perception",
            params={
                "check_vitals": check_vitals,
                "check_resurrection": check_resurrection,
            },
            timeout=1.0,
        )
        response.raise_for_status()
        data = response.json()

        # 处理 API 返回的数据，转换为 PerceptionSnapshot
        target_box = (0, 0, 1, 1) if data.get("has_target") else None

        # 默认使用屏幕中心区域作为复活按钮备用点击坐标
        resurrection_box = (
            (900, 500, 1020, 580) if data.get("resurrection_btn_visible") else None
        )

        h = data.get("health")
        m = data.get("mental")
        d = data.get("target_distance")
        c = data.get("captured_at")
        buffs = data.get("active_buff_codes")
        errs = data.get("errors")

        # 将服务器返回的 time.time() 转换为本地 time.monotonic()
        captured_at = now
        if c is not None:
            # 计算本地单调时钟与系统时钟的偏移量
            offset = time.monotonic() - time.time()
            captured_at = float(c) + offset

        return PerceptionSnapshot(
            captured_at=captured_at,
            health=float(h) if h is not None else -1.0,
            mental=float(m) if m is not None else -1.0,
            target_distance=int(d) if d is not None else -1,
            target_box=target_box,
            resurrection_box=resurrection_box,
            active_buff_codes=frozenset(buffs) if buffs is not None else frozenset(),
            errors=tuple(errs) if errs is not None else (),
        )
