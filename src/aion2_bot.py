import random
import select
import sys
import termios
import time
import tty

from bot_config import BotConfig
from console import console as console
from game_context import GameContext
from image_engine import ImageEngine
from km_driver import KmboxDriver
from player_controller import PlayerController
from role import Role
from role_swordstar import RoleSwordStar as AnyRole

# from role_bowstar import RoleBowStar as AnyRole
from strategy import CombatStrategy
from video_capture import VideoCapture


def read_stdin():
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        # 处理所有输入流中的字符，防止堆积
        while select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
        return char


class Aion2Bot(object):
    """
    Aion2 自动化机器人主控类。
    负责协调游戏画面的视觉感知、角色逻辑状态机、Kmbox 硬件指令控制及运行循环管理。
    """

    def __init__(self):
        """初始化机器人：加载配置、驱动硬件、实例化角色模型及 OCR 工具。"""
        self.config = BotConfig()
        self.km_driver = KmboxDriver(config=self.config.kmbox)
        self.video_capture = VideoCapture(config=self.config.video)
        self.image_engine = ImageEngine(config=self.config)

        self.context = GameContext(self.config.role.extract_interval_seconds)
        self.player_ctrl = PlayerController(self.km_driver, self.context)

        self.role: Role = AnyRole(
            role_config=self.config.role,
            km_driver=self.km_driver,
            player_ctrl=self.player_ctrl,
            context=self.context,
        )

        self.strategy = CombatStrategy(
            self.context, self.player_ctrl, self.role, self.config
        )

        self.is_paused = False

    def main_loop(self):
        """
        程序主循环。处理用户输入（暂停/退出）、运行控制逻辑、更新控制台仪表盘。
        支持在退出时自动恢复终端设置并释放系统资源。
        """
        old_settings = termios.tcgetattr(sys.stdin)
        period = 1.0 / self.config.runtime.max_ops_per_second
        try:
            print("初始化鼠标校正中。。。。")
            self.km_driver.initialize_mouse_track()
            # 设置终端为字符输入模式，以实现非阻塞读取
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
                    if self.update_perception(loop_start):
                        self.strategy.action()

                self._render_dashboard()

                # 限制循环频率以控制 CPU/GPU 负载
                elapsed = time.monotonic() - loop_start
                wait_time = random.uniform(period - 0.2, period + 0.2) - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)

        finally:
            # 退出清理工作
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.km_driver.close()
            self.video_capture.release()

    def _render_dashboard(self):
        """将当前机器人状态和角色信息渲染到控制台显示器。"""
        console.render_dashboard(self.strategy.get_state_str(), self.role)

    def _reset_perception_state(self, err_msg: str | None = None):
        """当发生感知异常（如视频流丢失）时，重置目标感知数据并返回空闲状态。"""
        self.context.reset_perception()
        self.strategy.set_idle_state()
        if err_msg:
            console.set_err_msg(err_msg)

    def update_perception(self, now) -> bool:
        img = self.video_capture.read_frame()
        if img is None:
            self._reset_perception_state(">>> 视频帧读取失败，已回退到待机状态")
            return False

        """执行视觉更新周期：读取画面、识别生命值、检测目标并计算距离。"""
        analysis = self.image_engine.analyze(
            img,
            include_vitals=int(now) % 3 == 1,
        )

        if analysis.liweijian_valid:
            self.context.active_skills["liweijian"] = time.monotonic() + 3

        if analysis.health is not None:
            # 更新血量感知
            self.context.health = analysis.health
        elif analysis.health_error:
            console.set_err_msg(analysis.health_error)

        if analysis.mental is not None:
            # 更新活力感知
            self.context.mental = analysis.mental
        elif analysis.mental_error:
            console.set_err_msg(analysis.mental_error)

        # self.get_status_from_box(frame, (50, 965, 370, 1020))

        target_box = analysis.target_box
        self.context.has_target = target_box is not None
        if target_box:
            self.context.resurrection_box = None
            if analysis.target_distance is not None:
                self.context.target_distance = analysis.target_distance
            else:
                self.context.target_distance = -1
                if analysis.target_distance_error:
                    console.set_err_msg(analysis.target_distance_error)
        else:
            self.context.target_distance = -1
            self.context.resurrection_box = analysis.resurrection_box

        return True


def main():
    """主函数，启动机器人实例。"""
    Aion2Bot().main_loop()


if __name__ == "__main__":
    main()
