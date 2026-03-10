from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from role import Aion2Role


class StateConsole:
    def __init__(self) -> None:
        self.note_msg = ""
        self.err_msg = ""

    @staticmethod
    def _clear_screen() -> None:
        print("\033[2J\033[H", end="")

    def show_pause(self):
        self._clear_screen()
        print("已暂停 (按空格键恢复)")

    def set_err_msg(self, err_msg: str):
        self.err_msg = err_msg

    def set_note_msg(self, note_msg: str):
        self.note_msg = note_msg

    def render_dashboard(self, state_str, role: "Aion2Role"):
        mouse_driver = getattr(role, "kmDriver", None)
        mouse_x = "-"
        mouse_y = "-"
        if mouse_driver is not None:
            mouse_x = getattr(mouse_driver, "mouse_x", "-")
            mouse_y = getattr(mouse_driver, "mouse_y", "-")

        status_line = (
            f"生命值: {role.health * 100:.2f}% | "
            f"活力值: {role.mental * 100:.2f}% | "
            f"距离: {role.target_distance}米 | "
            f"鼠标座标: X: {mouse_x}, Y: {mouse_y}"
        )

        content = (
            f"{status_line}"
            f"\n技能状态: {role.get_skill_cd_info()}"
            f"\n通知信息: {self.note_msg}"
            f"\n异常信息: {self.err_msg}"
            f"\n退出: Q键 暂停: 空格键"
        )

        self._clear_screen()
        print(f"=== {state_str} ===")
        print(content)
        # self.err_msg = ""
        # self.note_msg = ""


console = StateConsole()
