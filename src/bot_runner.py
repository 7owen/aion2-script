import random
import select
import sys
import termios
import time
import tty

from bot_config import config
from console import console as console
from game_context import BotState
from image_engine import ImageEngine
from player_actions import PlayerActions
from strategy import BaseStrategy, StrategyAction
from video_capture import VideoCapture


def read_stdin():
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        while select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
        return char
    return None


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

    def run(self) -> None:
        old_settings = termios.tcgetattr(sys.stdin)
        period = 1.0 / config.runtime.max_ops_per_second

        try:
            # print("初始化鼠标校正中。。。。")
            # self.player_action.reset_mouse()
            # time.sleep(0.5)
            # self.player_action.move_mouse_to_center()
            tty.setcbreak(sys.stdin.fileno())

            while True:
                loop_start = time.monotonic()
                char = read_stdin()
                if char == " ":
                    self.is_paused = not self.is_paused
                elif char == "q":
                    break

                if self.is_paused:
                    console.set_note_msg("已暂停脚本")
                else:
                    console.set_note_msg("")
                    if self.update_perception(loop_start):
                        for action in self.strategy.next_actions():
                            self._dispatch(action)

                self._render_dashboard()

                elapsed = time.monotonic() - loop_start
                wait_time = random.uniform(period - 0.2, period + 0.2) - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def update_perception(self, now: float) -> bool:
        img = self.video_capture.read_frame()
        if img is None:
            self._reset_perception_state(">>> 视频帧读取失败，已回退到待机状态")
            return False

        snapshot = self.image_engine.analyze(
            img,
            include_vitals=int(now) % 3 == 1,
        )
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
