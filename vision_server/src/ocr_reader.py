import os
import sys
from typing import List, Optional

from bot_config import OcrConfig


class EasyOcrEngine:
    """适用于 macOS (M系列芯片) 和带有高性能 GPU 的 Linux 环境。
    依赖 PyTorch，识别精度高但占用大。"""

    def __init__(self, ocr_config: OcrConfig):
        # 延迟加载，避免弱 CPU 初始化报错
        import easyocr

        try:
            self.reader = easyocr.Reader(
                list(ocr_config.languages), gpu=ocr_config.use_gpu
            )
            print(f"EasyOCR 正在使用的设备: {self.reader.device}")
        except Exception as exc:
            if ocr_config.use_gpu:
                print(f">>> EasyOCR GPU 初始化失败，降级到 CPU: {exc}")
                self.reader = easyocr.Reader(list(ocr_config.languages), gpu=False)
            else:
                raise

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        return self.reader.readtext(image, detail=detail, allowlist=allowlist)


class TesseractOcrEngine:
    """适用于弱性能 CPU (如 Intel N4100) 的 Linux 服务器。
    纯 CPU 计算，不需要 AVX 指令集。需要在系统级安装 tesseract。"""

    def __init__(self, ocr_config: OcrConfig):
        import os

        # 限制 Tesseract 内部的 OpenMP 线程数，防止弱 CPU 上产生严重抢占和上下文切换导致卡死
        os.environ["OMP_THREAD_LIMIT"] = "1"

        lang_map = {"en": "eng", "ch_sim": "chi_sim"}
        self.lang = (
            "+".join([lang_map.get(l, l) for l in ocr_config.languages]) or "eng"
        )

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        import pytesseract

        custom_config = "--psm 7"
        if allowlist:
            custom_config += f" -c tessedit_char_whitelist={allowlist}"

        try:
            text = pytesseract.image_to_string(
                image, lang=self.lang, config=custom_config
            )
            text = text.strip()
            if text:
                return [text]
            return []
        except pytesseract.TesseractNotFoundError:
            print(
                ">>> 错误: 找不到 Tesseract 可执行文件。请执行 `sudo apt-get install tesseract-ocr tesseract-ocr-eng` 安装。"
            )
            return []
        except Exception as e:
            print(f">>> Tesseract 识别异常: {e}")
            return []


class RapidOcrEngine:
    """现代 OCR 引擎，基于 ONNX Runtime。
    针对小区域识别，强制使用 CPU 模式以避免 GPU 调度延迟和数据搬运开销。
    """

    def __init__(self, ocr_config: OcrConfig):
        # 强制限制多线程并发。在运行 3D 游戏时，过多的并行线程会导致严重的上下文切换开销（Thrashing），
        # 这是导致之前出现 10s+ 延迟的核心原因。强制单线程反而能获得最稳定的响应。
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        os.environ["ONNXRUNTIME_NUM_THREADS"] = "1"

        try:
            from rapidocr_onnxruntime import RapidOCR

            # 强制使用 CPU 模式
            # providers = ["CPUExecutionProvider"]
            providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]

            # 设置 onnxruntime 提供者
            self.ocr = RapidOCR(
                print_verbose=False,
                text_score=0.5,
                providers=providers,
                intra_op_num_threads=1,
            )
            print(f"RapidOCR 初始化成功，使用的提供者: {providers}")
        except ImportError as e:
            print(f">>> 错误: {e}。请执行 `pip install rapidocr_onnxruntime`")
            raise e

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        # RapidOCR 输入为 numpy array
        # 对于已经裁剪好的小图，禁用文字检测 (use_det=False) 和方向分类 (use_cls=False) 可以极大提高速度
        try:
            result, elapse = self.ocr(image, use_det=False, use_cls=False)
            if result is None or not result:
                return []

            # 当 use_det=False 时，RapidOCR 返回 result 通常为 [['文本内容', 置信度]]
            # 需要稳健地解析这种嵌套结构以避免解包错误
            text = ""
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, (list, tuple)) and len(first_item) > 0:
                    text = str(first_item[0])
                else:
                    text = str(first_item)

            if not text:
                return []

            if allowlist:
                text = "".join([c for c in text if c in allowlist])

            if text:
                return [text]
        except Exception as e:
            print(f">>> RapidOCR 识别与解析异常: {e}")
            print(f">>> 原始返回结果: {result if 'result' in locals() else 'None'}")
        return []


class OcrReaderWrapper:
    def __init__(self, ocr_config: OcrConfig):
        """
        初始化 OCR 引擎封装。
        根据操作系统自动选择合适的底层 OCR 库。
        macOS (darwin) 优先使用 EasyOCR (支持 MPS)。
        Linux 优先使用 Tesseract (轻量级，避免弱 CPU 崩溃)。
        """
        # Windows 和 macOS 现在统一使用 RapidOCR CPU 模式以获得最佳响应速度
        if sys.platform in ("win32", "darwin"):
            self.engine = RapidOcrEngine(ocr_config)
        else:
            self.engine = TesseractOcrEngine(ocr_config)

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        """
        提取图像中的文本。
        返回纯字符串列表，完全屏蔽底层依赖。
        """
        return self.engine.readtext(image, detail=detail, allowlist=allowlist)
