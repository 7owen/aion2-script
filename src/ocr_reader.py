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


class OcrReaderWrapper:
    def __init__(self, ocr_config: OcrConfig):
        """
        初始化 OCR 引擎封装。
        根据操作系统自动选择合适的底层 OCR 库。
        macOS (darwin) 优先使用 EasyOCR (支持 MPS)。
        Linux 优先使用 Tesseract (轻量级，避免弱 CPU 崩溃)。
        """
        if sys.platform == "darwin":
            self.engine = EasyOcrEngine(ocr_config)
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
