import cv2
import mss
import numpy as np
import torch
from ultralytics.models.yolo import YOLO


def main():
    # 1. 加载官方 YOLO26n 模型
    print("正在加载 YOLO26n 模型...")
    try:
        # 注意：原代码中的 YOLO26n.pt 似乎是笔误，这里修正为标准的 YOLO26n.pt
        # 如果你确实有自定义模型 YOLO26n.pt，请改回原文件名
        model = YOLO("./aion2.pt")

        # 检查是否可以使用 Apple M 系列芯片的 GPU (MPS)
        if torch.backends.mps.is_available():
            print("检测到 Apple Silicon GPU，正在使用 MPS 加速...")
            model.to("mps")
        else:
            print("未检测到 MPS，将使用 CPU 运行。")

    except Exception as e:
        print(f"模型加载失败: {e}")
        return

    # 2. 初始化屏幕截图工具 (mss)
    print("初始化屏幕捕捉...")
    with mss.mss() as sct:
        # 获取第1个显示器（通常是主显示器）的信息
        monitor_number = 1
        try:
            mon = sct.monitors[monitor_number]
        except IndexError:
            print(f"错误: 找不到显示器 {monitor_number}。")
            return

        print("正在截取全屏以供选择区域，请稍候...")
        # 截取全屏用于选择
        screenshot = sct.grab(mon)
        img = np.array(screenshot)
        # mss 返回的是 BGRA，OpenCV 需要 BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        print("-" * 50)
        print("请在弹出的 'Select ROI' 窗口中框选检测区域：")
        print("1. 使用鼠标拖拽框选区域")
        print("2. 按 'SPACE' 或 'ENTER' 键确认选择")
        print("3. 按 'c' 键取消选择并退出")
        print("-" * 50)

        # 3. 让用户选择感兴趣区域 (ROI)
        # 注意：在 Mac Retina 屏幕上，如果全屏截图很大，窗口可能会超出屏幕，请尝试拖动或直接框选
        roi = cv2.selectROI("Select ROI", img, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow("Select ROI")

        # roi 格式为 (x, y, w, h)
        x, y, w, h = roi

        # 检查是否选择了有效区域
        if w == 0 or h == 0:
            print("未选择区域或取消了选择，程序退出。")
            return

        print(f"已选择区域: x={x}, y={y}, w={w}, h={h}")

        # 定义后续循环中要抓取的精确区域
        # monitor_region 需要包含 'top', 'left', 'width', 'height'
        monitor_region = {
            "top": mon["top"] + y,
            "left": mon["left"] + x,
            "width": w,
            "height": h,
            "mon": monitor_number,
        }

        print("开始实时检测选定区域。按 'q' 键退出。")
        # 为不同类别设置不同置信度
        class_conf = {
            "Enemy_Tag": 0.5,
            "Fight_Tag": 0.5,
            "Friendly_Tag": 0.5,
            "Loot_Tag": 0.65,
            "Resource_Tag": 0.65,
            "Self_Tag": 0.65,
            "Target_Tag": 0.65,
        }

        while True:
            # 4. 截取选定区域 (实时)
            img_region = sct.grab(monitor_region)

            # 转为 numpy 数组
            frame = np.array(img_region)

            # 转为 BGR 格式 (OpenCV/YOLO 使用)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # 5. YOLO 目标检测
            results = model(frame, stream=True, verbose=False)

            # 6. 可视化结果与数据获取
            for result in results:
                # 找出每种 tag 评分最高的一条 (且满足阈值)
                best_indices_dict = {}  # {tag: (index, conf)}
                for i, box in enumerate(result.boxes):
                    class_id = int(box.cls[0])
                    tag = result.names[class_id]
                    threshold = class_conf.get(tag, 0.5)
                    conf = float(box.conf[0])

                    if conf >= threshold:
                        # 如果该 tag 还没记录，或者当前置信度更高，则更新
                        if (
                            tag not in best_indices_dict
                            or conf > best_indices_dict[tag][1]
                        ):
                            best_indices_dict[tag] = (i, conf)

                # 获取筛选后的索引
                keep_indices = [idx for idx, _ in best_indices_dict.values()]

                # 打印筛选后的信息
                for idx in keep_indices:
                    box = result.boxes[idx]
                    tag = result.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    coords = box.xyxy[0].tolist()
                    print(f"Tag (Best): {tag}, Conf: {conf:.2f}, Box: {coords}")

                # 仅保留满足条件的检测结果用于显示
                # result[keep_indices] 会返回一个新的 Results 对象，只包含筛选后的框
                filtered_result = result[keep_indices]

                # 在图像上仅绘制满足过滤条件的框
                # annotated_frame = filtered_result.plot()
                annotated_frame = result.plot()

                # 显示图像
                cv2.imshow("YOLO26 Screen Detection", annotated_frame)

            # 7. 按 'q' 键退出
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # 释放资源
    cv2.destroyAllWindows()
    print("程序已退出。")


if __name__ == "__main__":
    main()
