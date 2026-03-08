import math
import random
from typing import List, Tuple

import numpy as np


class HumanMouseSimulator:
    def __init__(self):
        # 影响因子配置
        self.rough_phase_ratio = 0.75  # 粗略移动占总时间的比例
        self.reaction_time_jitter = 0.05  # 反应时间抖动
        self.correction_strength = 0.8  # 修正阶段的平滑度

    def _ease_out_cubic(self, x: float) -> float:
        """三次缓出函数，模拟快启动慢结束"""
        return 1 - pow(1 - x, 3)

    def _ease_in_out_quad(self, x: float) -> float:
        """二次缓入缓出"""
        return 2 * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 2) / 2

    def _bezier_point(
        self, start: float, control1: float, control2: float, end: float, t: float
    ) -> float:
        """计算三阶贝塞尔曲线上的点"""
        return (
            pow(1 - t, 3) * start
            + 3 * pow(1 - t, 2) * t * control1
            + 3 * (1 - t) * pow(t, 2) * control2
            + pow(t, 3) * end
        )

    def generate_path(
        self, target_offset: Tuple[int, int], duration_ms: int
    ) -> List[Tuple[int, int]]:
        """
        生成模拟真人的鼠标移动轨迹
        :param target_offset: (dx, dy) 目标偏移量
        :param duration_ms: 期望耗时(毫秒)
        :return: List of (dx, dy)
        """

        # 1. 初始化参数
        sx, sy = 0, 0
        ex, ey = target_offset
        dist = math.hypot(ex - sx, ey - sy)

        # 动态调整步数：每秒约 120 个点 (高刷新率模拟)
        # 如果距离极短，减少步数以防鼠标乱飞
        step_count = int(duration_ms / 1000 * 120)
        if step_count < 10:
            step_count = 10

        # 2. 定义“粗略目标点”(Fake Target)
        # 模拟人眼定位误差，通常在终点附近半径 R 范围内，距离越远误差越大
        offset_scale = min(20, dist * 0.04)  # 最大偏差减小

        rx = random.uniform(-offset_scale, offset_scale)
        ry = random.uniform(-offset_scale, offset_scale)

        # 尽量别越过终点：如果随机点离起点比终点还远，说明越过了，往回修
        if (ex + rx - sx) ** 2 + (ey + ry - sy) ** 2 > dist**2:
            rx *= -0.5
            ry *= -0.5

        fake_end_x = ex + rx
        fake_end_y = ey + ry

        # 3. 定义控制点 (用于贝塞尔曲线产生弧度)
        # 产生一些随机的弧度，而不是直线
        ctrl1_x = sx + (fake_end_x - sx) * 0.3 + random.uniform(-dist * 0.2, dist * 0.2)
        ctrl1_y = sy + (fake_end_y - sy) * 0.3 + random.uniform(-dist * 0.2, dist * 0.2)
        ctrl2_x = sx + (fake_end_x - sx) * 0.8 + random.uniform(-dist * 0.2, dist * 0.2)
        ctrl2_y = sy + (fake_end_y - sy) * 0.8 + random.uniform(-dist * 0.2, dist * 0.2)

        # 4. 生成时间序列 (Time Distortion)
        # 不使用线性的 t，而是生成一个有停顿、有变速的 t 序列
        t_values = np.linspace(0, 1, step_count)

        # 加入随机停顿 (Stutter/Pause)
        # 随机选择一个时间段，让 t 的增长极其缓慢甚至停滞
        if random.random() < 0.4:  # 40% 的概率出现明显停顿
            pause_start_idx = random.randint(
                int(step_count * 0.2), int(step_count * 0.6)
            )
            pause_length = random.randint(5, 15)
            # 在 pause_start_idx 处重复插入接近的值，模拟停顿
            t_slice = t_values[pause_start_idx]
            pause_arr = np.linspace(t_slice, t_slice + 0.01, pause_length)  # 极小进展
            t_values = np.insert(t_values, pause_start_idx, pause_arr)
            # 重新归一化到 0-1 (因为插入了数据，长度变了，这里为了简单直接截断或重采样，
            # 但为了保持逻辑连贯，我们仅仅接受数组变长，代表时间变长)

        path = []

        # 上一次的整数坐标
        last_int_x = sx
        last_int_y = sy

        # 5. 轨迹生成循环
        total_steps = len(t_values)
        rough_steps = int(total_steps * self.rough_phase_ratio)

        # 修正起点默认为假终点，但在切换阶段时会更新为实际位置
        correction_start_x = fake_end_x
        correction_start_y = fake_end_y

        for i, t_linear in enumerate(t_values):
            # --- 阶段判断 ---
            if i < rough_steps:
                # === 阶段 1: 粗略移动 (向 Fake Target 移动) ===
                # 使用 Ease-Out 曲线，模拟起步快，接近时减速
                prog = self._ease_out_cubic(t_linear / self.rough_phase_ratio)

                target_x = self._bezier_point(sx, ctrl1_x, ctrl2_x, fake_end_x, prog)
                target_y = self._bezier_point(sy, ctrl1_y, ctrl2_y, fake_end_y, prog)

                # 添加大幅度的手部抖动 (高频噪声)
                jitter_amp = (1 - prog) * 2.0  # 初始抖动大，越接近越小
                target_x += random.gauss(0, jitter_amp)
                target_y += random.gauss(0, jitter_amp)

            else:
                # === 阶段 2: 精细修正 (从 当前位置 向 Real End 修正) ===
                if i == rough_steps:
                    correction_start_x = last_int_x
                    correction_start_y = last_int_y

                # 重新计算进度 0.0 -> 1.0
                correction_t = (i - rough_steps) / (total_steps - rough_steps)

                # 修正阶段使用 Ease-In-Out，平滑过渡
                prog = self._ease_in_out_quad(correction_t)

                # 线性插值从 修正起点 -> 真终点 (这里不用贝塞尔，因为距离很短了)
                target_x = correction_start_x + (ex - correction_start_x) * prog
                target_y = correction_start_y + (ey - correction_start_y) * prog

                # 添加微小的修正抖动
                target_x += random.gauss(0, 0.5)
                target_y += random.gauss(0, 0.5)

            # --- 计算增量 (Physics Pixel Output) ---

            # 1. 计算当前帧的理想浮点位置
            next_float_x = target_x
            next_float_y = target_y

            # 2. 转换为整数坐标
            next_int_x = int(round(next_float_x))
            next_int_y = int(round(next_float_y))

            # 3. 计算 dx, dy
            dx = next_int_x - last_int_x
            dy = next_int_y - last_int_y

            # 4. 只有当确实发生位移时才记录 (防止大量 0,0 输出，除非模拟由于摩擦力的静止)
            # 这里我们允许输出 0,0 代表停顿
            path.append((dx, dy))

            # 更新状态
            last_int_x = next_int_x
            last_int_y = next_int_y

        # 6. 最终强制修正 (Final Snap)
        # 循环结束后，如果因为抖动或浮点误差没有正好落在终点，追加最后一步
        if last_int_x != ex or last_int_y != ey:
            path.append((ex - last_int_x, ey - last_int_y))

        return path


# --- 使用示例 ---

if __name__ == "__main__":
    import time

    simulator = HumanMouseSimulator()

    # 模拟输入
    target_offset = (700, 500)
    duration = 500  # 0.5秒

    path = simulator.generate_path(target_offset, duration)

    # 验证是否到达终点 (需安装 pynput)
    try:
        from pynput.mouse import Controller

        print("\n检测到 pynput，准备模拟鼠标移动 (3秒后开始)...")
        time.sleep(3)

        mouse = Controller()
        start_real = mouse.position
        print(f"起始实际坐标: {start_real}")

        # 计算每一步的休眠时间 (简单计算，未扣除执行时间)
        interval = (duration / 1000.0) / len(path)

        tx, ty = start_real
        for dx, dy in path:
            mouse.move(dx, dy)
            tx += dx
            ty += dy
            time.sleep(interval)

        print(f"移动结束，最终坐标: {mouse.position}")

    except ImportError:
        print("\n未安装 pynput，跳过鼠标控制演示。")
    except Exception as e:
        print(f"\n鼠标控制演示出错: {e}")
