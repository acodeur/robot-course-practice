from pathlib import Path
import argparse

import yaml


def package_root():
    return Path(__file__).resolve().parents[1]


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def validate_detection(det, index):
    if not isinstance(det, dict):
        return f"第 {index} 个检测结果必须是字典结构。"
    bbox = det.get("bbox_xyxy")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return f"第 {index} 个检测框 bbox_xyxy 必须包含 4 个数值。"
    try:
        x1, y1, x2, y2 = [float(v) for v in bbox]
    except (TypeError, ValueError):
        return f"第 {index} 个检测框 bbox_xyxy 含有非数字值。"
    if x2 <= x1 or y2 <= y1:
        return f"第 {index} 个检测框宽高必须为正数。"
    return None


def detection_confidence(det):
    try:
        return float(det.get("confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0


def choose_detection(data):
    detections = (data or {}).get("detections", [])
    if not detections:
        raise ValueError("没有检测框。")

    valid = []
    errors = []
    for index, det in enumerate(detections):
        error = validate_detection(det, index)
        if error:
            errors.append(error)
            continue
        valid.append(det)

    if not valid:
        detail = " ".join(errors)
        raise ValueError(f"没有可用检测框。{detail}")

    sports_balls = [
        det for det in valid
        if str(det.get("class_name", "")).strip().lower() == "sports ball"
    ]
    if sports_balls:
        return max(sports_balls, key=detection_confidence)

    return max(valid, key=detection_confidence)


def load_detection(input_path, fallback_path):
    candidates = [("输入文件", input_path)]
    if fallback_path != input_path:
        candidates.append(("兜底文件", fallback_path))

    failures = []
    for label, path in candidates:
        if not path.exists():
            failures.append(f"{label}不存在: {path}")
            continue
        try:
            data = load_yaml(path)
            det = choose_detection(data)
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f"{label}不可用: {path} ({exc})")
            continue

        if label != "输入文件":
            print("输入检测结果不可用，改用兜底 bbox:", path)
        return data, det, path

    raise ValueError("无法获得有效 bbox。 " + "；".join(failures))


def compute_target_pixel(det):
    x1, y1, x2, y2 = [float(v) for v in det["bbox_xyxy"]]
    u = (x1 + x2) / 2.0
    v = (y1 + y2) / 2.0
    w = x2 - x1
    h = y2 - y1
    return {
        "class_name": det.get("class_name", "unknown"),
        "confidence": detection_confidence(det),
        "bbox_xyxy": [x1, y1, x2, y2],
        "target_pixel": {"u": u, "v": v},
        "bbox_size": {"w": w, "h": h},
    }


def parse_args():
    root = package_root()
    parser = argparse.ArgumentParser(description="Compute target pixel from bbox_xyxy.")
    parser.add_argument("--input", default=str(root / "yolo/outputs/detections.yaml"))
    parser.add_argument("--fallback", default=str(root / "config/sample_bbox.yaml"))
    parser.add_argument("--output", default=str(root / "yolo/outputs/target_pixel.yaml"))
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    fallback_path = Path(args.fallback)

    try:
        data, det, source_path = load_detection(input_path, fallback_path)
    except ValueError as exc:
        raise SystemExit(str(exc))
    result = compute_target_pixel(det)
    result["image_width"] = int(data.get("image_width", 640))
    result["image_height"] = int(data.get("image_height", 480))
    result["source_yaml"] = str(source_path)
    result["selection_rule"] = "优先选择 class_name=sports ball；如果没有 sports ball，则选择置信度最高的有效检测框。"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("class_name:", result["class_name"])
    print("confidence:", f"{result['confidence']:.3f}")
    print("bbox_xyxy:", result["bbox_xyxy"])
    print("target_pixel: (u, v) = ({:.2f}, {:.2f})".format(result["target_pixel"]["u"], result["target_pixel"]["v"]))
    print("saved to:", output)


if __name__ == "__main__":
    main()
