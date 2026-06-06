from pathlib import Path
import argparse

import yaml


def package_root():
    return Path(__file__).resolve().parents[1]


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def parse_args():
    root = package_root()
    parser = argparse.ArgumentParser(description="Compute camera ray from target pixel and camera intrinsics.")
    parser.add_argument("--target", default=str(root / "yolo/outputs/target_pixel.yaml"))
    parser.add_argument("--intrinsics", default=str(root / "config/camera_intrinsics.yaml"))
    parser.add_argument("--output", default=str(root / "yolo/outputs/camera_ray.yaml"))
    return parser.parse_args()


def main():
    args = parse_args()
    target = load_yaml(args.target)
    intr = load_yaml(args.intrinsics)

    u = float(target["target_pixel"]["u"])
    v = float(target["target_pixel"]["v"])
    fx = float(intr["fx"])
    fy = float(intr["fy"])
    cx = float(intr["cx"])
    cy = float(intr["cy"])

    x = (u - cx) / fx
    y = (v - cy) / fy
    ray = [x, y, 1.0]

    result = {
        "target_pixel": {"u": u, "v": v},
        "intrinsics": {"fx": fx, "fy": fy, "cx": cx, "cy": cy},
        "camera_ray": ray,
        "meaning": "camera_ray=[x,y,1] 只表示方向，还不是完整 3D 点。",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("target_pixel: (u, v) = ({:.2f}, {:.2f})".format(u, v))
    print("camera_ray: [{:.6f}, {:.6f}, 1.000000]".format(x, y))
    print("saved to:", output)


if __name__ == "__main__":
    main()
