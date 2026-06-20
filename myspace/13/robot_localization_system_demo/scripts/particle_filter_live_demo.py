from __future__ import annotations

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np

from localization_core import (
    build_demo_data,
    compute_particle_weights,
    ensure_output_dir,
    estimate_pose,
    initialize_particles,
    load_config,
    metrics_text,
    position_errors,
    predict_particles,
    systematic_resample,
)


def draw_robot(ax, pose, color, label=None, size=0.22):
    x, y, theta = pose
    ax.arrow(
        x,
        y,
        size * math.cos(theta),
        size * math.sin(theta),
        head_width=0.12,
        head_length=0.12,
        fc=color,
        ec=color,
        linewidth=1.8,
        length_includes_head=True,
        label=label,
    )


def draw_map_state(
    ax,
    data,
    step,
    particles,
    estimated_trajectory,
    odom_errors,
    pf_errors,
):
    true = data["true_trajectory"]
    odom = data["odom_trajectory"]
    landmarks = data["landmarks"]
    observations = data["observations"][step]

    ax.clear()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.22)
    ax.set_xlabel("x / m")
    ax.set_ylabel("y / m")

    ax.scatter(particles[:, 0], particles[:, 1], s=9, color="#6baed6", alpha=0.35, label="particles")
    ax.scatter(landmarks[:, 0], landmarks[:, 1], marker="*", s=150, color="#2ca02c", label="landmarks")
    ax.plot(true[: step + 1, 0], true[: step + 1, 1], color="#2ca02c", linewidth=2.5, label="true")
    ax.plot(odom[: step + 1, 0], odom[: step + 1, 1], "--", color="#d62728", linewidth=2.0, label="odometry")
    ax.plot(
        estimated_trajectory[: step + 1, 0],
        estimated_trajectory[: step + 1, 1],
        color="#1f77b4",
        linewidth=2.3,
        label="particle filter",
    )

    estimated_pose = estimated_trajectory[step]
    draw_robot(ax, true[step], "#2ca02c", label="current true")
    draw_robot(ax, estimated_pose, "#1f77b4", label="current estimate")

    for landmark_id, _, _ in observations:
        landmark = landmarks[landmark_id]
        ax.plot(
            [estimated_pose[0], landmark[0]],
            [estimated_pose[1], landmark[1]],
            color="#74c476",
            linestyle=":",
            linewidth=1.2,
            alpha=0.8,
        )

    ax.set_title(
        f"step {step:03d} | odom error {odom_errors[step]:.2f} m | PF error {pf_errors[step]:.2f} m"
    )
    ax.legend(loc="upper left", fontsize=8)


def draw_error_curve(ax, odom_errors, pf_errors, step):
    ax.clear()
    ax.plot(odom_errors[: step + 1], color="#d62728", linewidth=2.0, label="odometry error")
    ax.plot(pf_errors[: step + 1], color="#1f77b4", linewidth=2.0, label="PF error")
    ax.set_xlim(0, len(odom_errors))
    max_err = max(float(np.max(odom_errors)), float(np.max(pf_errors)), 0.5)
    ax.set_ylim(0, max_err * 1.1)
    ax.set_xlabel("step")
    ax.set_ylabel("position error / m")
    ax.set_title("Error curve")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=8)


def run_particle_filter_live(config: dict, output_dir, show: bool):
    data = build_demo_data(config)
    rng = np.random.default_rng(int(config["random_seed"]) + 100)
    particles = initialize_particles(config, rng, data["true_trajectory"][0])
    weights = np.full(len(particles), 1.0 / len(particles))

    estimated = [estimate_pose(particles, weights)]
    true = data["true_trajectory"]
    odom = data["odom_trajectory"]
    odom_errors = position_errors(true, odom)
    pf_errors = [float(np.linalg.norm(true[0, :2] - estimated[0][:2]))]

    if show:
        plt.ion()

    fig, (ax_map, ax_err) = plt.subplots(
        1,
        2,
        figsize=(12, 5),
        gridspec_kw={"width_ratios": [2.1, 1.0]},
    )

    pause = float(config.get("animation", {}).get("pause", 0.03))
    for step, control in enumerate(data["odom_controls"], start=1):
        particles = predict_particles(particles, control, config, rng)
        weights = compute_particle_weights(
            particles,
            data["observations"][step],
            data["landmarks"],
            config,
        )
        estimate = estimate_pose(particles, weights)
        estimated.append(estimate)
        pf_errors.append(float(np.linalg.norm(true[step, :2] - estimate[:2])))

        estimated_arr = np.array(estimated)
        draw_map_state(ax_map, data, step, particles, estimated_arr, odom_errors, np.array(pf_errors))
        draw_error_curve(ax_err, odom_errors, np.array(pf_errors), step)
        fig.suptitle(
            "Particle filter: prediction, observation scoring, resampling",
            fontsize=13,
            fontweight="bold",
        )
        fig.tight_layout()

        if show:
            plt.pause(pause)

        particles, weights = systematic_resample(particles, weights, rng)

    estimated_trajectory = np.array(estimated)
    data["estimated_trajectory"] = estimated_trajectory

    fig.savefig(output_dir / "02_particle_filter_result.png", dpi=160)

    fig_err, ax = plt.subplots(figsize=(8, 4))
    ax.plot(odom_errors, color="#d62728", linewidth=2.0, label="odometry error")
    ax.plot(position_errors(true, estimated_trajectory), color="#1f77b4", linewidth=2.0, label="PF error")
    ax.set_title("Position error: odometry vs particle filter")
    ax.set_xlabel("step")
    ax.set_ylabel("error / m")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig_err.tight_layout()
    fig_err.savefig(output_dir / "03_error_curve.png", dpi=160)

    (output_dir / "metrics.txt").write_text(metrics_text(data), encoding="utf-8")

    if show:
        plt.ioff()
        plt.show()
    else:
        plt.close(fig)
    plt.close(fig_err)
    return data


def main():
    parser = argparse.ArgumentParser(description="Live particle filter localization demo.")
    parser.add_argument("--config", default=None, help="Path to demo_config.json")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--particles", type=int, default=None, help="Override particle count")
    parser.add_argument("--no-show", action="store_true", help="Only save images, do not open matplotlib window")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else load_config()
    if args.particles is not None:
        config["num_particles"] = int(args.particles)
    output_dir = ensure_output_dir(args.output_dir)
    show = not args.no_show
    data = run_particle_filter_live(config, output_dir, show=show)
    print(metrics_text(data))
    print(f"saved to: {output_dir}")


if __name__ == "__main__":
    main()
