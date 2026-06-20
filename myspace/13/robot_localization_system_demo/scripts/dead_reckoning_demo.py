from __future__ import annotations

import argparse

import matplotlib.pyplot as plt

from localization_core import build_demo_data, ensure_output_dir, load_config, position_errors


def draw_dead_reckoning_frame(ax_map, ax_err, data: dict, errors, step: int):
    true = data["true_trajectory"]
    odom = data["odom_trajectory"]
    landmarks = data["landmarks"]

    ax_map.clear()
    ax_err.clear()

    ax_map.plot(true[: step + 1, 0], true[: step + 1, 1], color="#2ca02c", linewidth=2.5, label="true trajectory")
    ax_map.plot(
        odom[: step + 1, 0],
        odom[: step + 1, 1],
        "--",
        color="#d62728",
        linewidth=2.2,
        label="dead reckoning",
    )
    ax_map.scatter(landmarks[:, 0], landmarks[:, 1], marker="*", s=160, color="#1f77b4", label="landmarks")
    ax_map.scatter(true[0, 0], true[0, 1], s=80, color="#2ca02c", label="start")
    ax_map.scatter(true[step, 0], true[step, 1], s=80, color="#145a32", label="current true")
    ax_map.scatter(odom[step, 0], odom[step, 1], s=80, color="#d62728", label="current odom")
    ax_map.plot(
        [true[step, 0], odom[step, 0]],
        [true[step, 1], odom[step, 1]],
        color="#d62728",
        linestyle=":",
        linewidth=1.6,
        alpha=0.85,
    )
    ax_map.set_title(f"Trajectory drift | step {step:03d} | error {errors[step]:.2f} m")
    ax_map.set_xlabel("x / m")
    ax_map.set_ylabel("y / m")
    ax_map.set_xlim(0, 10)
    ax_map.set_ylim(0, 7)
    ax_map.set_aspect("equal", adjustable="box")
    ax_map.grid(True, alpha=0.25)
    ax_map.legend(loc="upper left", fontsize=8)

    ax_err.plot(errors[: step + 1], color="#d62728", linewidth=2.2)
    ax_err.scatter(step, errors[step], s=45, color="#d62728")
    ax_err.set_title("Accumulated odometry error")
    ax_err.set_xlabel("step")
    ax_err.set_ylabel("error / m")
    ax_err.set_xlim(0, len(errors))
    ax_err.set_ylim(0, max(float(errors.max()) * 1.1, 0.5))
    ax_err.grid(True, alpha=0.25)


def plot_dead_reckoning(data: dict, save_path, show: bool = False, pause: float = 0.03, frame_stride: int = 3):
    true = data["true_trajectory"]
    errors = position_errors(true, data["odom_trajectory"])

    fig, (ax_map, ax_err) = plt.subplots(
        1,
        2,
        figsize=(12, 5),
        gridspec_kw={"width_ratios": [2.2, 1.0]},
    )

    if show:
        plt.ion()
        frames = list(range(0, len(true), max(1, frame_stride)))
        if frames[-1] != len(true) - 1:
            frames.append(len(true) - 1)
        for step in frames:
            draw_dead_reckoning_frame(ax_map, ax_err, data, errors, step)
            fig.suptitle("Only using odometry: error accumulates step by step", fontsize=14, fontweight="bold")
            fig.tight_layout()
            plt.pause(pause)
    else:
        draw_dead_reckoning_frame(ax_map, ax_err, data, errors, len(true) - 1)

    fig.suptitle("Only using odometry: error accumulates step by step", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(save_path, dpi=160)
    if show:
        plt.ioff()
        plt.show()
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Show dead reckoning drift.")
    parser.add_argument("--config", default=None, help="Path to demo_config.json")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--no-show", action="store_true", help="Only save image, do not open matplotlib window")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else load_config()
    data = build_demo_data(config)
    output_dir = ensure_output_dir(args.output_dir)
    save_path = output_dir / "01_dead_reckoning_drift.png"
    pause = float(config.get("animation", {}).get("pause", 0.03))
    plot_dead_reckoning(data, save_path, show=not args.no_show, pause=pause)
    print(f"saved to: {save_path}")


if __name__ == "__main__":
    main()
