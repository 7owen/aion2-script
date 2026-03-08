import re
import select
import sys
from pydoc import text

import cv2
import numpy as np


def batch_ocr(img_list):
    # 1. 统一高度（选最高的那个，其他的补黑边或者缩放）
    max_h = max(img.shape[0] for img in img_list)
    padded_imgs = []

    # 2. 补齐高度并在右侧加黑色间隔
    separator = np.zeros((max_h, 50), dtype=np.uint8)  # 50像素宽的黑条

    for img in img_list:
        h, w = img.shape
        # 上下补黑边居中
        top = (max_h - h) // 2
        bottom = max_h - h - top
        padded = cv2.copyMakeBorder(
            img, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=0
        )
        padded_imgs.append(padded)
        padded_imgs.append(separator)  # 加间隔

    # 3. 横向拼接
    return cv2.hconcat(padded_imgs[:-1])  # 去掉最后一个多余的间隔


def preprocess_image_for_ocr(pic):
    if pic is None:
        return None

    gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)

    # 1. 放大图像（在过滤前放大，利用插值算法让边缘更平滑）
    zoomed = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # # 2. 转换到 HSV 颜色空间进行颜色提取
    # hsv = cv2.cvtColor(zoomed, cv2.COLOR_BGR2HSV)

    # # 3. 定义白色的 HSV 范围
    # # 对于白字：饱和度(S)应该很低，亮度(V)应该很高
    # lower_white = np.array([0, 0, 200])  # 降低亮度阈值，让笔画边缘进入范围
    # upper_white = np.array([180, 150, 255])  # 严格控制饱和度，排除蓝色背景

    # # 4. 创建掩码（Mask）
    # mask = cv2.inRange(hsv, lower_white, upper_white)

    # # 5. 膨胀处理 (Dilation)：加粗笔画，连接断开的线条
    # # 如果预览图中字迹依然断开，可以尝试将 (2,2) 改为 (3,3)
    # kernel = np.ones((2, 2), np.uint8)
    # mask = cv2.dilate(mask, kernel, iterations=1)

    # 6. 颜色反转：将黑底白字转为白底黑字
    processed = cv2.bitwise_not(zoomed)

    return processed


def get_tag_box(yolo_results, tag):
    if not yolo_results or not yolo_results[0].boxes:
        return None

    # 使用生成器表达式过滤，提升性能
    names = yolo_results[0].names
    targets = [box for box in yolo_results[0].boxes if names[int(box.cls[0])] == tag]

    if not targets:
        return None
    target_box = max(targets, key=lambda x: x.conf[0])
    x1, y1, x2, y2 = map(int, target_box.xyxy[0].tolist())
    return x1, y1, x2, y2


def extract_text_via_ocr(
    ocr_reader, pic, allowlist, pattern, window_name, show_window=False
):
    """统一 OCR 处理流程"""
    processed_pic = preprocess_image_for_ocr(pic)
    if processed_pic is None:
        return None, f">>> {window_name} OCR 处理失败，预处理图片失败"

    if show_window:
        cv2.imshow(window_name, processed_pic)
        cv2.waitKey(1)

    try:
        ocr_result = ocr_reader.readtext(processed_pic, detail=0, allowlist=allowlist)
        print(ocr_result)
        text_combined = "".join([str(t) for t in ocr_result]).replace(",", "")
        # print(text_combined)

        match = re.search(pattern, text_combined, re.IGNORECASE)
        if match:
            return match.groups(), None
        else:
            return None, f">>> {window_name} OCR 提取失败，原文: '{text_combined}'"
    except Exception as e:
        return None, f">>> {window_name} OCR 处理出错: {e}"


def read_stdin():
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        # 处理所有输入流中的字符，防止堆积
        while select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
        return char


def crop_frame(
    frame_1080p,
    x_offset=720,
    y_offset=0,
    roi_width=480,
    roi_height=150,
):
    # 裁剪图像 (Numpy 切片操作，极快，耗时在零点几毫秒)
    crop_img = frame_1080p[
        y_offset : y_offset + roi_height,
        x_offset : x_offset + roi_width,
    ]
    return crop_img


# def restore_coordinates(box):
#     x_min, y_min, x_max, y_max = box[:4]

#     # 4. 坐标还原：加上裁剪的偏移量，回到 1920x1080 的坐标系
#     orig_x_min = x_min + x_offset
#     orig_y_min = y_min + y_offset
#     orig_x_max = x_max + x_offset
#     orig_y_max = y_max + y_offset

#     return [orig_x_min, orig_y_min, orig_x_max, orig_y_max, box[4], box[5]]


def match_and_locate(template_path, target_frame, min_match_count=10):
    """
    模板从文件读取，目标图直接使用 cv2.VideoCapture(...).read() 返回的 frame。
    """
    img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if img_template is None:
        print("错误：无法读取模板图片，请检查路径。")
        return None

    if target_frame is None:
        print("错误：目标帧为空。")
        return None

    if len(target_frame.shape) == 3:
        img_target = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
    else:
        img_target = target_frame

    return feature_match_and_locate(img_template, img_target, min_match_count)


def perfect_match_and_locate(template_path, target_frame, tolerance=0.0):
    """
    模板从文件读取，目标图直接使用 cv2.VideoCapture(...).read() 返回的 frame。
    """
    img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if img_template is None:
        print("错误：无法读取模板图片，请检查路径。")
        return None

    if target_frame is None:
        print("错误：目标帧为空。")
        return None

    if len(target_frame.shape) == 3:
        img_target = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
    else:
        img_target = target_frame

    return pixel_perfect_match_and_locate(img_template, img_target, tolerance)


def pixel_perfect_match_and_locate(img_template, img_target, tolerance=0.0):
    """
    使用像素级完全匹配定位模板位置。
    - tolerance=0.0: 仅接受完全一致的像素块
    - tolerance>0.0: 允许少量像素差异，取值建议在 0.0 到 1.0 之间
    - 使用 TM_SQDIFF_NORMED，误差越接近 0 越好
    返回: ((x_min, y_min), (x_max, y_max)) 或 None
    """

    th, tw = img_template.shape[:2]
    ih, iw = img_target.shape[:2]
    if th > ih or tw > iw:
        print("匹配失败 - 模板尺寸大于目标图。")
        return None

    # TM_SQDIFF_NORMED: 值越小越好，完全相同则 min_val 为 0
    result = cv2.matchTemplate(img_target, img_template, cv2.TM_SQDIFF_NORMED)
    min_val, _, min_loc, _ = cv2.minMaxLoc(result)
    # print(f"像素匹配最小归一化误差: {min_val:.8f}")

    if min_val <= tolerance:
        x_min, y_min = min_loc
        x_max, y_max = x_min + tw, y_min + th
        return x_min, y_min, x_max, y_max

    # print(f"匹配失败 - 超出误差阈值 (min_val={min_val:.8f}, tolerance={tolerance:.8f})")
    return None


def feature_match_and_locate(img_template, img_target, min_match_count=10):
    """
    使用 SIFT 特征匹配定位界面元素
    :param template_path: 模板图片路径（你要找的元素，如一个小图标）
    :param target_path: 目标图片路径（整张截图）
    :param min_match_count: 最少需要多少个匹配点才算识别成功
    """
    if img_template is None or img_target is None:
        print("错误：无法读取图片，请检查路径。")
        return None

    required_matches = max(min_match_count, 4)

    def _ratio_filter(matches, ratio):
        filtered = []
        for pair in matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < ratio * n.distance:
                filtered.append(m)
        return filtered

    # 2. 先尝试 ORB（速度快），失败或点数不足时回退 SIFT（鲁棒性更高）
    orb = cv2.ORB_create(  # type: ignore
        nfeatures=3000,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=15,
        fastThreshold=5,
    )
    kp1, des1 = orb.detectAndCompute(img_template, None)
    kp2, des2 = orb.detectAndCompute(img_target, None)

    if des1 is None or des2 is None:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        kp1, des1 = orb.detectAndCompute(clahe.apply(img_template), None)
        kp2, des2 = orb.detectAndCompute(clahe.apply(img_target), None)

    good_matches = []
    if des1 is not None and des2 is not None:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)  # type: ignore
        matches = bf.knnMatch(des1, des2, k=2)  # type: ignore
        good_matches = _ratio_filter(matches, 0.75)

    detector_name = "ORB"

    if len(good_matches) < required_matches and hasattr(cv2, "SIFT_create"):
        sift = cv2.SIFT_create()  # type: ignore
        kp1_sift, des1_sift = sift.detectAndCompute(img_template, None)
        kp2_sift, des2_sift = sift.detectAndCompute(img_target, None)
        if des1_sift is not None and des2_sift is not None:
            des1_sift = np.float32(des1_sift)
            des2_sift = np.float32(des2_sift)
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)  # type: ignore
            matches_sift = flann.knnMatch(des1_sift, des2_sift, k=2)  # type: ignore
            good_matches_sift = _ratio_filter(matches_sift, 0.7)
            if len(good_matches_sift) > len(good_matches):
                kp1, kp2 = kp1_sift, kp2_sift
                good_matches = good_matches_sift
                detector_name = "SIFT"

    print(f"{detector_name} 找到 {len(good_matches)} 个优质匹配点。")

    # 6. 判断是否找到足够多的匹配点
    if len(good_matches) >= required_matches:
        # 获取匹配点的坐标
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(  # type: ignore
            -1, 1, 2
        )
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(  # type: ignore
            -1, 1, 2
        )

        # 7. 计算单应性矩阵 (Homography)
        # RANSAC 算法可以排除异常点，计算出物体在目标图中的变换矩阵
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        if M is not None:
            # 获取模板图的尺寸
            h, w = img_template.shape

            # 定义模板图的四个角点
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(  # type: ignore
                -1, 1, 2
            )

            # 使用矩阵 M 将四个角点映射到目标图中
            # 返回顺序与 pts 一致: 左上, 左下, 右下, 右上
            dst = cv2.perspectiveTransform(pts, M).reshape(4, 2)
            corners = [(int(x), int(y)) for x, y in dst]
            return corners

        else:
            print("错误：无法计算变换矩阵。")
            return None

    else:
        print(f"匹配失败 - 匹配点不足 ({len(good_matches)}/{required_matches})")
        return None
