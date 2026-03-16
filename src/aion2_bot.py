import random
import select
import sys
import termios
import time
import tty
from enum import Enum

from bot_config import BotConfig
from console import console as console
from image_engine import ImageEngine
from km_driver import KmboxDriver
from role import Role
from role_bowstar import RoleBowStar as AnyRole

# from role_swordstar import RoleSwordStar as aRole
from video_capture import VideoCapture


def read_stdin():
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        # 处理所有输入流中的字符，防止堆积
        while select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
        return char


class State(Enum):
    """机器人运行状态枚举"""

    IDLE = "idle"  # 空闲状态，用于寻怪或执行日常操作
    FIGHT = "fight"  # 战斗状态，正在攻击目标
    EXTRACT = "extract"  # 采集状态，正在进行资源提取
    DEATH = "death"


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
        self.role: Role = AnyRole(
            role_config=self.config.role,
            km_driver=self.km_driver,
        )
        self.state = State.IDLE
        self.cur_try_combat_count = 0
        self.is_paused = False
        self.role.start()
        self.resurrection_box = None

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
                    if self.update_role(loop_start):
                        self.action()

                self._render_dashboard()

                # 限制循环频率以控制 CPU/GPU 负载
                elapsed = time.monotonic() - loop_start
                wait_time = random.uniform(period - 0.1, period + 0.1) - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)

        finally:
            # 退出清理工作
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.role.stop()
            self.video_capture.release()

    def _render_dashboard(self):
        """将当前机器人状态和角色信息渲染到控制台显示器。"""
        state_str = {
            State.IDLE: "🔍 寻找目标",
            State.FIGHT: "⚔️ 战斗中",
            State.EXTRACT: "🧪 提取中",
        }.get(self.state, str(self.state))
        console.render_dashboard(state_str, self.role)

    def _reset_perception_state(self, err_msg: str | None = None):
        """当发生感知异常（如视频流丢失）时，重置目标感知数据并返回空闲状态。"""
        self.role.has_target = False
        self.role.target_distance = -1
        if self.state == State.FIGHT:
            self.state = State.IDLE
        if err_msg:
            console.set_err_msg(err_msg)

    def update_role(self, now) -> bool:
        img = self.video_capture.read_frame()
        if img is None:
            self._reset_perception_state(">>> 视频帧读取失败，已回退到待机状态")
            return False

        """执行视觉更新周期：读取画面、识别生命值、检测目标并计算距离。"""
        self.role.tick()
        analysis = self.image_engine.analyze(
            img,
            include_vitals=int(now) % 3 == 1,
        )

        if analysis.liweijian_valid:
            self.role.active_skills["liweijian"] = time.monotonic() + 3

        if analysis.health is not None:
            # 更新血量感知
            self.role.health = analysis.health
        elif analysis.health_error:
            console.set_err_msg(analysis.health_error)

        if analysis.mental is not None:
            # 更新活力感知
            self.role.mental = analysis.mental
        elif analysis.mental_error:
            console.set_err_msg(analysis.mental_error)

        # self.get_status_from_box(frame, (50, 965, 370, 1020))

        target_box = analysis.target_box
        self.role.has_target = target_box is not None
        if target_box:
            self.resurrection_box = None
            if analysis.target_distance is not None:
                self.role.target_distance = analysis.target_distance
            else:
                self.role.target_distance = -1
                if analysis.target_distance_error:
                    console.set_err_msg(analysis.target_distance_error)
        else:
            self.role.target_distance = -1
            self.resurrection_box = analysis.resurrection_box

        return True

    def action(self):
        """状态机核心逻辑：根据当前状态执行相应动作。"""
        if self.state == State.IDLE:
            self.role.buff()
            if self.resurrection_box:
                self.state = State.DEATH
            elif self.role.has_target:
                self.state = State.FIGHT
            elif self.role.need_extract:
                self.state = State.EXTRACT
            else:
                # 尝试搜寻，若次数耗尽则旋转视角
                if self.cur_try_combat_count < self.config.runtime.max_try_combat_count:
                    self.cur_try_combat_count += 1
                    self.role.search()
                    time.sleep(0.5)
                else:
                    self.cur_try_combat_count = 0
                    self.role.rotate_view()
        elif self.state == State.FIGHT:
            if self.role.has_target:
                self.role.fight()
            else:
                self.role.loot()
                self.set_idle_state()
        elif self.state == State.EXTRACT:
            self.role.extraction()
            self.set_idle_state()
        elif self.state == State.DEATH:
            self.role.resurrect(self.resurrection_box)
            self.resurrection_box = None
            self.set_idle_state()

    def set_idle_state(self):
        self.state = State.IDLE
        self.cur_try_combat_count = 0


def main():
    """主函数，启动机器人实例。"""
    Aion2Bot().main_loop()


if __name__ == "__main__":
    main()
