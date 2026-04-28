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


class RapidOcrEngine:
    """现代 OCR 引擎，基于 ONNX Runtime。
    针对 N4100 弱性能 CPU 进行优化：开启多线程并行处理。
    """

    def __init__(self, ocr_config: OcrConfig):
        # N4100 为 4 核处理器，在独占模式下开启多线程以提升识别速度

        try:
            from rapidocr_onnxruntime import RapidOCR

            # 强制使用 CPU 模式
            providers = ["CPUExecutionProvider"]

            # 设置 onnxruntime 提供者
            # intra_op_num_threads=0 让 ORT 自动选择最优线程数（通常对应物理核心数）

            self.ocr = RapidOCR(
                print_verbose=False,
                text_score=0.5,
                providers=providers,
                intra_op_num_threads=0,
            )

            print("RapidOCR 初始化成功 (N4100 多核模式): 默认中英文版")
        except ImportError as e:
            print(f">>> 错误: {e}。请执行 `pip install rapidocr_onnxruntime`")
            raise e

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        # RapidOCR 输入为 numpy array
        # 对于已经裁剪好的小图，禁用文字检测 (use_det=False) 和方向分类 (use_cls=False) 可以极大提高速度
        result = []
        try:
            result, _ = self.ocr(image, use_det=False, use_cls=False)
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
        self.engine = RapidOcrEngine(ocr_config)

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        return self.engine.readtext(image, detail=detail, allowlist=allowlist)
