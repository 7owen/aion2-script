from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from role import Aion2Role


class StateConsole:
    def __init__(self) -> None:
        self.console = Console()
        self.note_msg = ""
        self.err_msg = ""

    def show_pause(self):
        self.console.clear()
        self.console.print("[bold yellow]已暂停 (按空格键恢复)[/]")

    def set_err_msg(self, err_msg: str):
        self.err_msg = err_msg

    def set_note_msg(self, note_msg: str):
        self.note_msg = note_msg

    def render_dashboard(self, state_str, role: "Aion2Role"):
        health_style = "[red]" if role.is_low_health() else "[green]"
        mouse_driver = getattr(role, "kmDriver", None)
        mouse_x = "-"
        mouse_y = "-"
        if mouse_driver is not None:
            mouse_x = getattr(mouse_driver, "mouse_x", "-")
            mouse_y = getattr(mouse_driver, "mouse_y", "-")

        status_line = (
            f"生命值: {health_style}{role.health * 100:.2f}%[/] | "
            f"活力值: [cyan]{role.mental * 100:.2f}%[/] | "
            f"距离: [yellow]{role.target_distance}米[/] | "
            f"鼠标座标: [blue]X: {mouse_x}, Y: {mouse_y}[/]"
        )

        content = (
            f"{status_line}"
            f"\n技能状态: {role.get_skill_cd_info()}"
            f"\n最近使用: {role.get_recent_skills()}"
            f"\n通知信息: {self.note_msg}"
            f"\n[dim red]异常信息: {self.err_msg}[/]"
            f"\n退出: Q键 暂停: 空格键"
        )

        self.console.clear()
        self.console.print(f"[bold blue]=== [bold white]{state_str}[/] ===[/]")
        self.console.print(content)
        self.err_msg = ""
        self.note_msg = ""


console = StateConsole()
