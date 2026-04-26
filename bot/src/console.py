from __future__ import annotations

from typing import TYPE_CHECKING

from km_driver import KmboxDriver

if TYPE_CHECKING:
    from game_context import BotState


class StateConsole:
    def __init__(self) -> None:
        self.note_msg = ""
        self.err_msg = ""

    @staticmethod
    def _clear_screen() -> None:
        print("\033[2J\033[H", end="", flush=True)

    def show_pause(self):
        self._clear_screen()
        print("已暂停 (按空格键恢复)")

    def set_err_msg(self, err_msg: str):
        self.err_msg = err_msg

    def set_note_msg(self, note_msg: str):
        self.note_msg = note_msg

    def render_dashboard(
        self,
        state_str: str,
        state: BotState,
        mouse_driver: KmboxDriver,
    ):
        role = state.role
        mouse_x = getattr(mouse_driver, "mouse_x", "-")
        mouse_y = getattr(mouse_driver, "mouse_y", "-")

        status_line = (
            f"生命值: {role.health * 100:.2f}% | "
            f"活力值: {role.mental * 100:.2f}% | "
            f"距离: {state.target.distance if state.target else -1}米 | "
            f"鼠标座标: X: {mouse_x}, Y: {mouse_y}"
        )

        content = (
            f"{status_line}"
            f"\n自身状态: {role.get_buff_info()}"
            f"\n敌方状态: {state.target.get_buff_info() if state.target else '无'}"
            f"\n技能状态: {role.get_skill_cd_info()}"
            f"\n通知信息: {self.note_msg}"
            f"\n异常信息: {self.err_msg}"
            f"\n退出: Q键 暂停: 空格键"
        )

        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self._clear_screen()
        print(f"=== {state_str} [{timestamp}] ===", flush=True)
        print(content, flush=True)


console = StateConsole()
