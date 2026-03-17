import time


class GameContext:
    """游戏世界状态上下文。包含每帧感知到的数据。"""

    def __init__(self, extract_interval_seconds):
        self.health = 1.0
        self.mental = 1.0
        self.has_target = False
        self.target_distance = -1
        self.resurrection_box: tuple[int, int, int, int] | None = None

        self.active_skills = {}

        self.next_extract_at = float("inf")
        self.extract_interval_seconds = extract_interval_seconds
        self.extract_countdowning()

    def reset_perception(self):
        """重置基于画面的瞬间感知数据"""
        self.has_target = False
        self.target_distance = -1
        self.resurrection_box = None

    def need_extract(self):
        return time.monotonic() >= self.next_extract_at

    def extract_countdowning(self):
        self.next_extract_at = time.monotonic() + self.extract_interval_seconds
