from ultralytics.models.yolo import YOLO

# 1. 加载你训练好的 .pt 模型
model = YOLO("aion2_s.pt")

# 2. 导出模型
# format="onnx" 是必须的
# opset=12 通常兼容性最好，macOS 建议使用 12 或更高
# model.export(format="onnx", opset=12, simplify=True)
model.export(format="coreml", nms=True)
