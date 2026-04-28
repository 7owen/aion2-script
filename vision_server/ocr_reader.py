import os
import sys
from typing import List, Optional

from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion, RapidOCR

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
    """现代 OCR 引擎，基于 RapidOCR 3.0+ (ONNX Runtime)。
    针对 N4100 弱性能 CPU 进行优化：开启多线程并行处理。
    """

    def __init__(self, ocr_config: OcrConfig):
        # N4100 为 4 核处理器，在独占模式下开启多线程以提升识别速度

        try:
            from rapidocr import RapidOCR

            # RapidOCR 3.0+ 默认使用 ONNX Runtime
            # print_verbose=False 关闭详细日志输出

            self.ocr = RapidOCR(
                params={
                    "Global.use_det": False,
                    "Global.use_cls": False,
                    "Global.text_score": 0.5,
                    # "Rec.engine_type": EngineType.ONNXRUNTIME,
                    # "Rec.lang_type": LangDet.EN,
                    # "Rec.model_type": ModelType.MOBILE,
                    # "Rec.ocr_version": OCRVersion.PPOCRV5,
                }
            )

            print("RapidOCR 3.0+ 初始化成功 (N4100 多核模式): 默认中英文版")
        except ImportError as e:
            print(f">>> 错误: {e}。请执行 `pip install rapidocr>=3.0.0`")
            raise e

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        # RapidOCR 3.0+ 输入为 numpy array 或 PIL Image
        # 对于已经裁剪好的小图，禁用文字检测 (det=False) 和方向分类 (cls=False) 可以极大提高速度
        result = None
        try:
            result = self.ocr(image, use_det=False, use_cls=False, use_rec=True)
            if result is None:
                return []

            # RapidOCR 3.0+ 返回 TextRecOutput 对象
            # result.txts 是字符串元组，直接拼接即可
            if not hasattr(result, "txts") or not result.txts:
                return []

            # 直接拼接所有识别到的文本
            text = "".join(result.txts)
            print(text)
            if allowlist:
                text = "".join([c for c in text if c in allowlist])

            if text:
                return [text]
        except Exception as e:
            print(f">>> RapidOCR 3.0+ 识别与解析异常: {e}")
            print(f">>> 原始返回结果: {result if result is not None else 'None'}")
        return []


class OcrReaderWrapper:
    def __init__(self, ocr_config: OcrConfig):
        self.engine = RapidOcrEngine(ocr_config)

    def readtext(
        self, image, detail: int = 0, allowlist: Optional[str] = None
    ) -> List[str]:
        return self.engine.readtext(image, detail=detail, allowlist=allowlist)
