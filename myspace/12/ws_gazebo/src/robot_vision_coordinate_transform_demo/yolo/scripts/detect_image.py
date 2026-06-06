from pathlib import Path
import argparse
import os
import subprocess
import sys

import cv2
import yaml
from ultralytics import YOLO


def parse_args():
    root = Path(__file__).resolve().parents[2]
    default_image = root / "yolo/images/gazebo_camera.png"
    if not default_image.exists():
        default_image = root / "yolo/images/soccer_practice_field.png"

    parser = argparse.ArgumentParser(description="Run YOLO detection on one image.")
    parser.add_argument("--image", default=str(default_image), help="input image path")
    parser.add_argument("--model", default=str(root / "yolo/models/yolo11n.pt"), help="YOLO model path")
    parser.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    parser.add_argument("--output-dir", default=str(root / "yolo/outputs/python_predict"), help="visual output directory")
    parser.add_argument("--yaml", default=str(root / "yolo/outputs/detections.yaml"), help="detection yaml output")
    parser.add_argument("--no-show", action="store_false", dest="show", help="do not open the annotated result window")
    parser.add_argument("--show-ms", type=int, default=0, help="display time in milliseconds; 0 waits for a key press")
    parser.set_defaults(show=True)
    return parser.parse_args()


def can_open_window():
    if sys.platform.startswith("linux"):
        display = os.environ.get("DISPLAY")
        if not display and not os.environ.get("WAYLAND_DISPLAY"):
            return False
        if display:
            try:
                probe = subprocess.run(
                    ["xdpyinfo"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                return probe.returncode == 0
            except FileNotFoundError:
                return False
        return True
    return True


def show_result_window(result, show_ms):
    if not can_open_window():
        print("未检测到图形显示环境，跳过屏幕显示。可查看 output-dir 中保存的可视化图片。")
        return

    annotated = result.plot()
    window_name = "YOLO detection result - press any key to close"
    try:
        cv2.imshow(window_name, annotated)
        print("检测结果窗口已打开，按任意键关闭。")
        cv2.waitKey(show_ms)
        cv2.destroyWindow(window_name)
    except cv2.error as exc:
        print("无法打开 OpenCV 显示窗口，已保留文件输出。错误信息:", exc)


def main():
    args = parse_args()
    image_path = Path(args.image).resolve()
    model_path = Path(args.model).resolve()
    output_dir = Path(args.output_dir).resolve()
    yaml_path = Path(args.yaml).resolve()
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    results = model.predict(
        source=str(image_path),
        conf=args.conf,
        save=True,
        project=str(output_dir.parent),
        name=output_dir.name,
        exist_ok=True,
    )

    result = results[0]
    names = result.names
    height, width = result.orig_shape

    detections = []
    for i, box in enumerate(result.boxes):
        cls_id = int(box.cls[0])
        class_name = names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        detections.append(
            {
                "index": i,
                "class_name": class_name,
                "confidence": round(confidence, 6),
                "bbox_xyxy": [round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)],
            }
        )

    data = {
        "image": str(image_path),
        "image_width": int(width),
        "image_height": int(height),
        "detections": detections,
    }
    yaml_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("image:", image_path)
    print("detections:", len(detections))
    print("-" * 80)
    for det in detections:
        print(f"[{det['index']}] class_name={det['class_name']}")
        print(f"    confidence={det['confidence']:.3f}")
        print(f"    bbox_xyxy={tuple(det['bbox_xyxy'])}")
    print("-" * 80)
    print("visual result saved to:", output_dir)
    print("detections yaml saved to:", yaml_path)
    if not detections:
        print("没有检测结果。可以先使用 config/sample_bbox.yaml 继续坐标计算。")
    if args.show:
        show_result_window(result, args.show_ms)


if __name__ == "__main__":
    main()
