"""RT-DETR (Real-Time DEtection TRansformer) 目标检测 Demo

用ultralytics内置的RT-DETR-L模型对资料包图片做推理，输出格式参照scripts/detect_image.py，方便与YOLO11n做对比
"""

import io
import sys
from pathlib import Path

from ultralytics import RTDETR

# Windows + 中文路径下避免控制台编码报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    base_dir = Path(__file__).resolve().parents[1]
    model_path = base_dir / "models/rtdetr-l.pt"  # 首次运行，ultralytics会自动下载
    image_paths = [
        base_dir / "images/soccer_practice_field.png",
        base_dir / "images/soccer_grass.png",
        base_dir / "images/soccer_studio_closeup.png",
        base_dir / "images/soccer_indoor_floor.png",
        base_dir / "images/color_ball_floor_bg.png",
        base_dir / "images/color_ball_clean.png",
    ]
    output_dir = base_dir / "outputs/rtdetr_predict"

    model = RTDETR(str(model_path))

    for image_path in image_paths:
        results = model.predict(
            source=str(image_path),
            conf=0.25,
            save=True,
            project=str(output_dir.parent.resolve()),
            name=output_dir.name,
            exist_ok=True,
            verbose=True,
        )

        result = results[0]
        names = result.names
        speed = result.speed  # dict: preprocess / inference / postprocess (ms)

        print("=" * 80)
        print("image:", image_path.relative_to(base_dir))
        print("detections:", len(result.boxes))
        print("speed(ms):  preprocess={:.1f}  inference={:.1f}  postprocess={:.1f}".format(
                speed["preprocess"], speed["inference"], speed["postprocess"]
            )
        )
        print("-" * 80)

        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls[0])
            class_name = names[cls_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            print(f"[{i}] class_name={class_name}")
            print(f"    confidence={confidence:.3f}")
            print(f"    bbox_xyxy=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")

        print("=" * 80)
        print("visual result saved to:", output_dir.relative_to(base_dir))


if __name__ == "__main__":
    main()
