from pathlib import Path
import subprocess
import sys

import yaml


def run(cmd):
    print("\n$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def print_summary(root):
    target = load_yaml(root / "yolo/outputs/target_pixel.yaml")
    result = load_yaml(root / "yolo/outputs/coordinate_transform_result.yaml")

    pixel = target["target_pixel"]
    p_robot = result["P_robot"]
    comparison = result.get("comparison")
    error_norm = comparison.get("error_norm") if comparison else None

    print("\n" + "=" * 64)
    print("离线坐标转换链路汇总")
    print("=" * 64)
    print("selected class:", target.get("class_name", "unknown"))
    print("target pixel:  u={:.2f}, v={:.2f}".format(float(pixel["u"]), float(pixel["v"])))
    print("depth:         method={}, Z={:.3f} m".format(result["depth_method"], float(result["depth_Z_m"])))
    print(
        "P_robot:       Xr={:.3f}, Yr={:.3f}, Zr={:.3f}".format(
            float(p_robot["Xr"]),
            float(p_robot["Yr"]),
            float(p_robot["Zr"]),
        )
    )
    if error_norm is not None:
        print("truth error:   {:.3f} m".format(float(error_norm)))
    else:
        print("truth error:   未读取 Gazebo 真值")
    print("=" * 64)


def main():
    root = Path(__file__).resolve().parents[1]
    py = sys.executable

    detections = root / "yolo/outputs/detections.yaml"
    fallback = root / "config/sample_bbox.yaml"

    run([
        py,
        str(root / "scripts/compute_target_pixel.py"),
        "--input",
        str(detections),
        "--fallback",
        str(fallback),
    ])
    run([py, str(root / "scripts/compute_camera_ray.py")])
    run([py, str(root / "scripts/compute_robot_position.py")])
    print_summary(root)


if __name__ == "__main__":
    main()
