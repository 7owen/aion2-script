import random
import sys
import termios
import time
import tty
from enum import Enum

import easyocr

from bot_config import BotConfig, OcrConfig
from console import console as console
from km_driver import KmboxDriver

# from role_bowstar import RoleBowStar as Role
from role_swordstar import RoleSwordStar as Role
from utils import (
    crop_frame,
    extract_text_via_ocr,
    get_tag_box,
    perfect_match_and_locate,
    read_stdin,
)
from video_capture import VideoCapture


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
        self.role = Role(
            role_config=self.config.role,
            km_driver=self.km_driver,
        )
        self.ocr_reader = self._create_ocr_reader(self.config.ocr)
        self.state = State.IDLE
        self.cur_try_combat_count = 0
        self.is_paused = False
        self.role.start()
        self.resurrection_box = None

    def _create_ocr_reader(self, ocr_config: OcrConfig):
        """初始化 OCR 引擎。若配置 GPU 加速但初始化失败，则自动回退至 CPU 模式。"""
        try:
            return easyocr.Reader(list(ocr_config.languages), gpu=ocr_config.use_gpu)
        except Exception as exc:
            if ocr_config.use_gpu:
                console.set_err_msg(f">>> OCR GPU 初始化失败，降级到 CPU: {exc}")
                return easyocr.Reader(list(ocr_config.languages), gpu=False)
            raise

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
                    if not self.is_paused:
                        self.km_driver.initialize_mouse_track()
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
        """执行视觉更新周期：读取画面、识别生命值、检测目标并计算距离。"""
        self.role.tick()

        frame = self.video_capture.read_frame()
        if frame is None:
            self._reset_perception_state(">>> 视频帧读取失败，已回退到待机状态")
            return False

        self.resurrection_box = self.get_resurrection_box(frame)

        if int(now) % 3 == 1:
            # 更新血量感知
            health, health_err = self.get_health_value(frame)
            if not health_err:
                self.role.health = health
            else:
                console.set_err_msg(health_err)

            # 更新活力感知
            mental_value, mental_err = self.get_mental_value(frame)
            if not mental_err:
                self.role.mental = mental_value
            else:
                console.set_err_msg(mental_err)

        # 视觉目标检测, 裁剪游戏画面顶部区域用于识别目标和距离，减少算力开销
        target_frame = crop_frame(
            frame,
            x_offset=self.config.vision.frame_crop_x_offset,
            y_offset=self.config.vision.frame_crop_y_offset,
            roi_width=self.config.vision.frame_crop_width,
            roi_height=self.config.vision.frame_crop_height,
        )

        # target_box = self.get_target_box_v1(target_frame)
        target_box = self.get_target_box_v2(target_frame)
        self.role.has_target = target_box is not None
        if target_box:
            # 获取目标距离
            # distance_box = self.get_distance_box_v1(target_box)
            distance_box = self.get_distance_box_v2(target_box)
            dist, dist_err = self.get_distance_from_box(target_frame, distance_box)
            if not dist_err:
                self.role.target_distance = dist
            else:
                self.role.target_distance = -1
                console.set_err_msg(dist_err)
        else:
            self.role.target_distance = -1

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
                    time.sleep(1)
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

    def get_health_value(self, frame):
        """识别屏幕特定区域的生命值 OCR 文本并转化为百分比。"""
        rect = self.config.vision.health_rect
        pic = self.video_capture.capture_pic(frame, rect.x1, rect.y1, rect.x2, rect.y2)
        result, err_msg = extract_text_via_ocr(
            self.ocr_reader,
            pic,
            self.config.ocr.health_allowlist,
            self.config.ocr.health_pattern,
            "生命值",
            False,
        )
        if result and len(result) >= 2 and int(result[1]) != 0:
            return int(result[0]) / int(result[1]), None
        return -1, err_msg

    def get_mental_value(self, frame):
        """识别屏幕特定区域的活力值 OCR 文本并转化为百分比。"""
        rect = self.config.vision.mental_rect
        pic = self.video_capture.capture_pic(frame, rect.x1, rect.y1, rect.x2, rect.y2)
        result, err_msg = extract_text_via_ocr(
            self.ocr_reader,
            pic,
            self.config.ocr.health_allowlist,
            self.config.ocr.health_pattern,
            "活力值",
            False,
        )
        if result and len(result) >= 2 and int(result[1]) != 0:
            return int(result[0]) / int(result[1]), None
        return -1, err_msg

    def get_distance_box_v1(self, target_box):
        x1, y1, x2, y2 = target_box
        x1 += int((x2 - x1) * self.config.vision.distance_x_shift_ratio)
        x2 -= self.config.vision.distance_x2_trim
        y1 += self.config.vision.distance_y1_offset
        y2 -= int((y2 - y1) * self.config.vision.distance_y2_trim_ratio)
        return x1, y1, x2, y2

    def get_distance_box_v2(self, target_box):
        t_x1, t_y1, _, _ = target_box
        x1 = t_x1 - 50
        x2 = t_x1 - 12
        y1 = t_y1 - 20
        y2 = t_y1
        return x1, y1, x2, y2

    def get_distance_from_box(self, frame, distance_box):
        x1, y1, x2, y2 = distance_box
        pic = self.video_capture.capture_pic(frame, x1, y1, x2, y2)
        result, err_msg = extract_text_via_ocr(
            self.ocr_reader,
            pic,
            self.config.ocr.distance_allowlist,
            self.config.ocr.distance_pattern,
            "目标距离",
            False,
        )
        if result:
            return int(result[0]), None
        return -1, err_msg

    def get_target_box_v1(self, frame):
        yolo_results = self.video_capture.predict(
            frame,
            imgsz=self.config.vision.yolo_imgsz,
            conf=self.config.vision.yolo_conf,
        )
        return get_tag_box(yolo_results, "Top_Target_Tag")

    def get_target_box_v2(self, frame):
        return perfect_match_and_locate(
            "src/images/top-target-right-icon.png", frame, 0.05
        )

    def get_resurrection_box(self, frame):
        return perfect_match_and_locate("src/images/resurrection-btn.png", frame, 0.1)


def main():
    """主函数，启动机器人实例。"""
    bot = Aion2Bot()
    bot.main_loop()


if __name__ == "__main__":
    main()
