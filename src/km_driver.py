import random
import time

import kmbox_net

from bot_config import KmboxConfig
from human_mouse import HumanMouseSimulator


# ==================== Kmbox 驱动层 ====================
class KmboxDriver:
    def __init__(self, config: KmboxConfig | None = None) -> None:
        self.config = config or KmboxConfig.from_env()
        self.screen_width = self.config.screen_width
        self.screen_height = self.config.screen_height
        self.mouse_x = 0
        self.mouse_y = 0
        self.human_mouse = HumanMouseSimulator()

        self.client = None
        self.monitor = None
        self.closed = False

        self._connect()

    def _connect(self):
        try:
            self.client = kmbox_net.KmBoxNetClient(
                self.config.ip,
                self.config.port,
                self.config.mac,
            )

            # 监控功能
            def on_event(mouse, keyboard):
                if mouse.buttons != 0 or mouse.x != 0 or mouse.y != 0:
                    # print(f"{mouse.x},{mouse.y}")
                    self._update_mouse(mouse.x, mouse.y)

                # if keyboard.buttons != 0 or len(keyboard.data) > 0:
                #     print(f"Keyboard: {keyboard.data}")

            self.monitor = kmbox_net.KmBoxNetMonitor(self.config.monitor_port, on_event)
            self.client.monitor(self.config.monitor_port)

        except Exception:
            self.close()
            raise

    def _ensure_client(self):
        if self.closed:
            raise RuntimeError("KmboxDriver is closed")
        if self.client is None:
            raise RuntimeError("Kmbox client is not initialized")
        return self.client

    def close(self):
        """显式释放资源，确保监控停止；支持重复调用。"""
        if self.closed:
            return

        self.closed = True
        client = self.client
        monitor = self.monitor
        self.client = None
        self.monitor = None

        if client:
            try:
                client.monitor(0)
            except Exception:
                pass

        if monitor:
            try:
                monitor.shutdown()
            except Exception:
                pass

    def __del__(self):
        # 仅作为兜底，主流程应显式调用 close。
        try:
            self.close()
        except Exception:
            pass

    def _update_mouse(self, dx, dy):
        self.mouse_x = self.mouse_x + dx
        if self.mouse_x < 0:
            self.mouse_x = 0
        elif self.mouse_x > self.screen_width:
            self.mouse_x = self.screen_width

        self.mouse_y = self.mouse_y + dy
        if self.mouse_y < 0:
            self.mouse_y = 0
        elif self.mouse_y > self.screen_height:
            self.mouse_y = self.screen_height

    def mouse_reset(self):
        client = self._ensure_client()
        client.enc_mouse_move_auto(
            -self.screen_width + 1, -self.screen_height + 1, 1000
        )
        time.sleep(0.5)
        self.mouse_x = 0
        self.mouse_y = 0
        self.human_mouse_move(
            int(self.screen_width / 2), int(self.screen_height / 2), 2
        )

    def initialize_mouse_track(self):
        self.mouse_reset()

    def human_mouse_move(self, dx: int, dy: int, duration=0.5, update_mouse_xy=True):
        client = self._ensure_client()
        paths = self.human_mouse.generate_path((dx, dy), int(duration * 1000))
        if not paths:
            return

        interval = duration / len(paths)
        for per_dx, per_dy in paths:
            client.enc_mouse_move(per_dx, per_dy)
            time.sleep(interval)

        if update_mouse_xy:
            self._update_mouse(dx, dy)

    def human_mouse_move_to(self, x: int, y: int, duration=0.5, update_mouse_xy=True):
        self.human_mouse_move(
            x - self.mouse_x, y - self.mouse_y, duration, update_mouse_xy
        )

    def mouse_move_auto(self, dx, dy, duration=0.5, update_mouse_xy=True):
        client = self._ensure_client()
        client.enc_mouse_move_auto(dx, dy, int(duration * 1000))
        if update_mouse_xy:
            self._update_mouse(dx, dy)

    def mouse_move_auto_to(self, x, y, duration=0.5, update_mouse_xy=True):
        self.mouse_move_auto(
            x - self.mouse_x, y - self.mouse_y, duration, update_mouse_xy
        )

    def key_press(self, key, duration_ms=None):
        client = self._ensure_client()
        if duration_ms is None:
            duration_ms = random.randint(60, 120)
        client.enc_keydown(key)
        time.sleep(duration_ms / 1000)
        client.enc_keyup(key)

    def key_down(self, key):
        self._ensure_client().keydown(key)

    def key_up(self, key):
        self._ensure_client().keyup(key)

    def mouse_left(self, is_down: bool):
        self._ensure_client().mouse_left(is_down)

    def mouse_right(self, is_down: bool):
        self._ensure_client().mouse_right(is_down)

    def mouse_left_press(self):
        client = self._ensure_client()
        client.enc_mouse_left(True)
        time.sleep(random.randint(60, 120) / 1000)
        client.enc_mouse_left(False)

    def mouse_right_press(self):
        client = self._ensure_client()
        client.enc_mouse_right(True)
        time.sleep(random.randint(60, 120) / 1000)
        client.enc_mouse_right(False)


def get_kmbox_driver(config: KmboxConfig | None = None) -> KmboxDriver:
    return KmboxDriver(config=config)
