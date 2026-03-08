import cv2
import torch
from ultralytics.models.yolo import YOLO


def main():
    # 1. 加载官方 YOLO26n 模型 (Nano 版本，速度最快)
    # 第一次运行时会自动从 ultralytics 仓库下载权重文件
    print("正在加载 YOLO26n 模型...")
    try:
        model = YOLO("aion2.pt")

        # 检查是否可以使用 Apple M 系列芯片的 GPU (MPS)
        if torch.backends.mps.is_available():
            print("检测到 Apple Silicon GPU，正在使用 MPS 加速...")
            model.to("mps")
        else:
            print("未检测到 MPS，将使用 CPU 运行。")

    except Exception as e:
        print(f"模型加载失败: {e}")
        return

    # 2. 打开 USB 摄像头
    # 参数 0 通常对应计算机的默认摄像头
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("错误: 无法打开摄像头。请检查连接或权限。")
        return

    print("摄像头已启动。按 'q' 键退出程序。")

    # 设置窗口大小 (可选)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        # 3. 读取视频帧
        ret, frame = cap.read()

        if not ret:
            print("错误: 无法读取视频帧。")
            break

        # 获取并打印图片宽高
        # height, width = frame.shape[:2]
        # print(f"当前帧分辨率: 宽={width}, 高={height}")

        # 4. 进行 YOLO 目标检测
        # stream=True 可以减少内存占用，verbose=False 用于减少控制台输出
        results = model(frame, stream=True, verbose=False)

        # 5. 可视化结果
        # results 是一个生成器，因为我们只传入了一帧，所以取第一个结果
        for result in results:
            # plot() 方法会在图像上绘制检测到的边界框和标签
            # 返回的是一个 BGR 格式的 numpy 数组，可以直接用 OpenCV 显示
            annotated_frame = result.plot()

            # 显示图像
            cv2.imshow("YOLO26n Real-time Detection", annotated_frame)

        cv2.waitKey(1)
        # 6. 按 'q' 键退出
        # if cv2.waitKey(1) & 0xFF == ord("q"):
        #     break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("程序已退出。")


if __name__ == "__main__":
    main()
