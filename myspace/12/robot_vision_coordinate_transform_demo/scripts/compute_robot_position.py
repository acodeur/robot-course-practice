from pathlib import Path
import argparse
import math

import yaml


def package_root():
    return Path(__file__).resolve().parents[1]


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def mat_vec_mul(mat, vec):
    return [sum(float(mat[i][j]) * float(vec[j]) for j in range(3)) for i in range(3)]


def add_vec(a, b):
    return [float(a[i]) + float(b[i]) for i in range(3)]


def read_truth(path):
    p = Path(path)
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def depth_from_known_size(target, intrinsics, params):
    h_pixel = float(target["bbox_size"]["h"])
    fy = float(intrinsics["fy"])
    real_height = float(params["target"]["real_height_m"])
    return fy * real_height / h_pixel


def depth_from_fixed(params):
    return float(params["depth"]["fixed_z_m"])


def depth_from_ground_height(ray, extr, params):
    R = extr["R_robot_camera"]
    t = extr["t_robot_camera"]
    direction_robot = mat_vec_mul(R, ray)
    target_z = float(params["target"]["center_height_robot_m"])
    camera_z = float(t["z"])
    if abs(direction_robot[2]) < 1e-6:
        raise ValueError("射线几乎平行于高度约束平面，无法求交。")
    scale = (target_z - camera_z) / direction_robot[2]
    if scale <= 0:
        raise ValueError("求交结果在相机后方，检查 bbox 或高度约束。")
    return scale


def parse_args():
    root = package_root()
    parser = argparse.ArgumentParser(description="Compute P_camera and P_robot.")
    parser.add_argument("--target", default=str(root / "yolo/outputs/target_pixel.yaml"))
    parser.add_argument("--ray", default=str(root / "yolo/outputs/camera_ray.yaml"))
    parser.add_argument("--intrinsics", default=str(root / "config/camera_intrinsics.yaml"))
    parser.add_argument("--extrinsics", default=str(root / "config/extrinsics_robot_camera.yaml"))
    parser.add_argument("--params", default=str(root / "config/coordinate_transform_params.yaml"))
    parser.add_argument("--truth", default=str(root / "gazebo_truth/target_ball_truth.yaml"))
    parser.add_argument("--output", default=str(root / "yolo/outputs/coordinate_transform_result.yaml"))
    parser.add_argument("--method", default=None, choices=["known_size", "fixed_z", "ground_height"])
    return parser.parse_args()


def main():
    args = parse_args()
    target = load_yaml(args.target)
    ray_data = load_yaml(args.ray)
    intr = load_yaml(args.intrinsics)
    extr = load_yaml(args.extrinsics)
    params = load_yaml(args.params)

    ray = [float(v) for v in ray_data["camera_ray"]]
    method = args.method or params["depth"]["method"]

    if method == "known_size":
        Z = depth_from_known_size(target, intr, params)
    elif method == "fixed_z":
        Z = depth_from_fixed(params)
    else:
        Z = depth_from_ground_height(ray, extr, params)

    P_camera = [ray[0] * Z, ray[1] * Z, Z]
    R = extr["R_robot_camera"]
    t = extr["t_robot_camera"]
    t_vec = [float(t["x"]), float(t["y"]), float(t["z"])]
    P_robot = add_vec(mat_vec_mul(R, P_camera), t_vec)

    truth = read_truth(args.truth)
    truth_frame = None
    comparison = None
    if truth:
        truth_frame = truth.get("frame", "gazebo_world")
        tp = truth["position"]
        truth_vec = [float(tp["x"]), float(tp["y"]), float(tp["z"])]
        err = [P_robot[i] - truth_vec[i] for i in range(3)]
        comparison = {
            "gazebo_truth": truth_vec,
            "gazebo_truth_frame": truth_frame,
            "error_xyz": err,
            "error_norm": math.sqrt(sum(e * e for e in err)),
            "comparison_assumption": "本课程 launch 中 humanoid 以 Gazebo 世界原点、零姿态生成，因此 P_robot 可和 gazebo_world 真值做量级对比；机器人移动或旋转后不能直接比较。",
            "note": "这里只做量级对比；bbox、简化内外参和深度估计都会影响结果。",
        }

    result = {
        "depth_method": method,
        "depth_Z_m": Z,
        "frames": {
            "P_camera": "camera_link optical convention: X right, Y down, Z forward",
            "P_robot": "robot/base simplified frame: X forward, Y left, Z up",
            "gazebo_truth": truth_frame,
        },
        "P_camera": {"Xc": P_camera[0], "Yc": P_camera[1], "Zc": P_camera[2]},
        "P_robot": {"Xr": P_robot[0], "Yr": P_robot[1], "Zr": P_robot[2]},
        "comparison": comparison,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("depth_method:", method)
    print("Z: {:.3f} m".format(Z))
    print("P_camera: Xc={:.3f}, Yc={:.3f}, Zc={:.3f}".format(*P_camera))
    print("P_robot:  Xr={:.3f}, Yr={:.3f}, Zr={:.3f}".format(*P_robot))
    if comparison:
        print("Gazebo truth:", comparison["gazebo_truth"])
        print("error norm: {:.3f} m".format(comparison["error_norm"]))
    print("saved to:", output)


if __name__ == "__main__":
    main()
