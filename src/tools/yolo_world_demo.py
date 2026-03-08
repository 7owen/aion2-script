import cv2
import mss
import numpy as np
import torch
from ultralytics.models.yolo import YOLO


def main():
    # 1. 加载官方 YOLO26n 模型
    print("正在加载 YOLO-World 模型...")
    try:
        # 1. 加载预训练的 YOLO-World 模型
        # 可选模型: yolov8s-world.pt (小且快), yolov8m-world.pt (中等), yolov8l-world.pt (大且准)
        # 如果本地没有模型文件，ultralytics 会自动从网上下载
        model = YOLO("yolov8s-world.pt")

        # 检查是否可以使用 Apple M 系列芯片的 GPU (MPS)
        if torch.backends.mps.is_available():
            print("检测到 Apple Silicon GPU，正在使用 MPS 加速...")
            model.to("mps")
        else:
            print("未检测到 MPS，将使用 CPU 运行。")

    except Exception as e:
        print(f"模型加载失败: {e}")
        return

    # 2. 定义你想要检测的任意类别（开放词汇能力）
    # 比如这里我们除了检测常规物体，还可以检测具体特征的物体
    custom_classes = ["red health bar", "mini map"]
    print(f"设置自定义检测类别: {custom_classes}")
    model.set_classes(custom_classes)

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
