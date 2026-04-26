import queue
import random
import sys
import threading
import time

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty

import cv2

from bot_config import config
from console import console as console
from game_context import BotState
from image_engine import ImageEngine
from player_actions import PlayerActions
from strategy import BaseStrategy, StrategyAction
from video_capture import VideoCapture


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
        video_capture: VideoCapture,
        image_engine: ImageEngine,
        player_action: PlayerActions,
        strategy: BaseStrategy,
    ) -> None:
        self.state = state
        self.video_capture = video_capture
        self.image_engine = image_engine
        self.player_action = player_action
        self.strategy = strategy
        self.is_paused = False

        self._last_vitals_time = 0.0
        self._last_resurrection_time = 0.0

        self._cached_health = None
        self._cached_mental = None
        self._cached_resurrection = None

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
            # print("DEBUG: Start loop iteration", flush=True)

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
                # print("DEBUG: Calling update_perception", flush=True)
                if self.update_perception(loop_start):
                    # print("DEBUG: Calling strategy.next_actions", flush=True)
                    for action in self.strategy.next_actions():
                        # print(f"DEBUG: Dispatching action: {action}", flush=True)
                        self._dispatch(action)

            # print("DEBUG: Rendering dashboard", flush=True)
            self._render_dashboard()

            elapsed = time.monotonic() - loop_start
            wait_time = random.uniform(period - 0.2, period + 0.2) - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

    def update_perception(self, now: float) -> bool:
        img = self.video_capture.read_frame()
        if img is None:
            self._reset_perception_state(">>> 视频帧读取失败，已回退到待机状态")
            return False

        # if not sys.platform.startswith("linux"):
        #     cv2.imshow("Capture", img)
        #     cv2.waitKey(1)

        check_vitals = (now - self._last_vitals_time) > 1
        check_resurrection = (now - self._last_resurrection_time) > 5.0

        snapshot = self.image_engine.analyze(
            img,
            check_vitals=check_vitals,
            check_resurrection=check_resurrection,
        )

        if check_vitals:
            self._cached_health = snapshot.health
            self._cached_mental = snapshot.mental
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
                health=self._cached_health,
                mental=self._cached_mental,
                resurrection_box=self._cached_resurrection,
            )
        except TypeError:
            snapshot.health = self._cached_health
            snapshot.mental = self._cached_mental
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
