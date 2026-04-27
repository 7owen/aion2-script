import queue
import random
import sys
import threading
import time

import requests

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty

from bot_config import config
from console import console as console
from game_context import BotState, PerceptionSnapshot
from player_actions import PlayerActions
from strategy import BaseStrategy, StrategyAction


def keyboard_listener(input_queue: queue.Queue):
    if sys.platform == "win32":
        try:
            while True:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode("utf-8", errors="ignore")
                    if char:
                        input_queue.put(char)
                        if char == "q":
                            break
                time.sleep(0.1)
        except Exception:
            pass
        return

    old_settings = None
    try:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    except Exception:
        # 捕获 SSH 等无 TTY 环境下的 ioctl 异常，允许降级
        pass

    try:
        while True:
            # 使用 select 监听，防止死锁
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                char = sys.stdin.read(1)
                if not char:
                    break
                input_queue.put(char)
                if char == "q":
                    break
    except Exception:
        pass
    finally:
        if old_settings is not None:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except Exception:
                pass


class BotRunner:
    def __init__(
        self,
        *,
        state: BotState,
        video_capture=None,
        player_action: PlayerActions,
        strategy: BaseStrategy,
    ) -> None:
        self.state = state
        self.video_capture = video_capture
        self.player_action = player_action
        self.strategy = strategy
        self.is_paused = False

        self._last_vitals_time = 0.0
        self._last_resurrection_time = 0.0

        self._cached_resurrection = None
        self._session = requests.Session()

    def run(self) -> None:
        period = 1.0 / config.runtime.max_ops_per_second
        input_queue = queue.Queue()

        listener_thread = threading.Thread(
            target=keyboard_listener,
            args=(input_queue,),
            daemon=True,
        )
        listener_thread.start()

        while True:
            loop_start = time.monotonic()

            char = None
            while not input_queue.empty():
                char = input_queue.get_nowait()

            if char == " ":
                self.is_paused = not self.is_paused
                if self.is_paused:
                    console.set_note_msg("已暂停脚本")
                else:
                    console.set_note_msg("")
            elif char == "q":
                break

            if not self.is_paused:
                if self.update_perception(loop_start):
                    for action in self.strategy.next_actions():
                        self._dispatch(action)

            self._render_dashboard()

            elapsed = time.monotonic() - loop_start
            wait_time = random.uniform(period - 0.2, period + 0.2) - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

    def _fetch_perception_data(
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

        return PerceptionSnapshot(
            captured_at=data.get("captured_at", now),
            health=data.get("health"),
            mental=data.get("mental"),
            target_distance=data.get("target_distance", -1),
            target_box=target_box,
            resurrection_box=resurrection_box,
            active_buff_codes=frozenset(data.get("active_buff_codes", [])),
            errors=tuple(data.get("errors", [])),
        )

    def update_perception(self, now: float) -> bool:
        check_vitals = (now - self._last_vitals_time) > 2
        check_resurrection = (now - self._last_resurrection_time) > 5.0

        try:
            snapshot = self._fetch_perception_data(
                now, check_vitals, check_resurrection
            )
        except Exception as e:
            self._reset_perception_state(f">>> 视觉服务连接失败: {e}")
            return False

        if check_vitals:
            self._last_vitals_time = now

        if snapshot.target_box:
            self._cached_resurrection = None
        else:
            if check_resurrection:
                self._cached_resurrection = snapshot.resurrection_box
                self._last_resurrection_time = now

        try:
            from dataclasses import replace

            snapshot = replace(
                snapshot,
                resurrection_box=self._cached_resurrection,
            )
        except TypeError:
            snapshot.resurrection_box = self._cached_resurrection

        self.state.apply_perception(snapshot)
        console.set_err_msg(" | ".join(snapshot.errors))
        return True

    def _dispatch(self, action: StrategyAction) -> None:
        role = self.state.role
        if action == StrategyAction.BUFF:
            role.buff()
        elif action == StrategyAction.SEARCH:
            role.search()
        elif action == StrategyAction.START_FIGHT:
            if self.state.target is not None:
                role.start_fight(self.state.target)
        elif action == StrategyAction.LOOP_FIGHT:
            if self.state.target is not None:
                role.loop_fight(self.state.target)
        elif action == StrategyAction.END_FIGHT:
            role.end_fight(self.state.target)
        elif action == StrategyAction.LOOT:
            self.player_action.loot()
        elif action == StrategyAction.ROTATE_VIEW:
            self.player_action.rotate_view()
        elif action == StrategyAction.EXTRACT_EQUIPMENT:
            self.player_action.extract_equipment()
            self.state.schedule_next_extract()
        elif action == StrategyAction.RESURRECT_CHARACTER:
            self.player_action.resurrect_character(self.state.resurrection_btn)
            self.state.resurrection_btn = None
        elif action == StrategyAction.CANCEL_CUR_TARGET:
            self.player_action.press_escape()
            self.state.target.clear_target()
            self.strategy.set_idle_state()

    def _render_dashboard(self) -> None:
        console.render_dashboard(
            self.strategy.get_status_info(),
            self.state,
            self.player_action.kmDriver,
        )

    def _reset_perception_state(self, err_msg: str | None = None) -> None:
        self.state.reset_perception()
        self.strategy.set_idle_state()
        console.set_err_msg(err_msg or "")
