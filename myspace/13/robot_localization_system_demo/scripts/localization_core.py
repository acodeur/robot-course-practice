from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "demo_config.json"


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def wrap_angle(angle):
    return np.arctan2(np.sin(angle), np.cos(angle))


def motion_model(pose: np.ndarray, control: np.ndarray, dt: float) -> np.ndarray:
    x, y, theta = pose
    v, w = control
    next_pose = np.array(
        [
            x + v * dt * math.cos(theta),
            y + v * dt * math.sin(theta),
            wrap_angle(theta + w * dt),
        ],
        dtype=float,
    )
    return next_pose


def motion_model_batch(particles: np.ndarray, controls: np.ndarray, dt: float) -> np.ndarray:
    v = controls[:, 0]
    w = controls[:, 1]
    out = particles.copy()
    out[:, 0] += v * dt * np.cos(particles[:, 2])
    out[:, 1] += v * dt * np.sin(particles[:, 2])
    out[:, 2] = wrap_angle(out[:, 2] + w * dt)
    return out


def make_true_trajectory(config: dict) -> np.ndarray:
    steps = int(config["steps"])
    s = np.linspace(0.0, 1.0, steps)

    x = 1.0 + 8.0 * s
    y = 3.5 + 1.4 * np.sin(2.0 * np.pi * s) - 0.55 * np.sin(4.0 * np.pi * s)

    dx = np.gradient(x)
    dy = np.gradient(y)
    theta = np.arctan2(dy, dx)
    theta = np.unwrap(theta)
    theta = wrap_angle(theta)
    return np.column_stack([x, y, theta])


def controls_from_trajectory(trajectory: np.ndarray, dt: float) -> np.ndarray:
    delta = trajectory[1:, :2] - trajectory[:-1, :2]
    v = np.linalg.norm(delta, axis=1) / dt
    dtheta = wrap_angle(trajectory[1:, 2] - trajectory[:-1, 2])
    w = dtheta / dt
    return np.column_stack([v, w])


def make_odometry(config: dict, true_controls: np.ndarray, start_pose: np.ndarray, rng: np.random.Generator):
    dt = float(config["dt"])
    noise = config["motion_noise"]
    v_std = float(noise["v_std"])
    w_std = float(noise["w_std"])
    drift = float(noise["drift_per_step"])

    odom_controls = np.zeros_like(true_controls)
    odom_poses = np.zeros((len(true_controls) + 1, 3), dtype=float)
    odom_poses[0] = start_pose

    for i, control in enumerate(true_controls):
        v, w = control
        v_meas = v * (1.0 + 0.015) + rng.normal(0.0, v_std)
        w_meas = w + drift * (1.0 + i / max(1, len(true_controls))) + rng.normal(0.0, w_std)
        odom_controls[i] = [v_meas, w_meas]
        odom_poses[i + 1] = motion_model(odom_poses[i], odom_controls[i], dt)

    return odom_poses, odom_controls


def make_observations(
    config: dict,
    true_trajectory: np.ndarray,
    landmarks: np.ndarray,
    rng: np.random.Generator,
) -> list[list[tuple[int, float, float]]]:
    sensor_range = float(config["sensor_range"])
    r_std = float(config["observation_noise"]["range_std"])
    b_std = float(config["observation_noise"]["bearing_std"])
    observations: list[list[tuple[int, float, float]]] = []

    for pose in true_trajectory:
        x, y, theta = pose
        step_obs = []
        for idx, landmark in enumerate(landmarks):
            dx = landmark[0] - x
            dy = landmark[1] - y
            distance = math.hypot(dx, dy)
            if distance <= sensor_range:
                bearing = wrap_angle(math.atan2(dy, dx) - theta)
                step_obs.append(
                    (
                        idx,
                        float(distance + rng.normal(0.0, r_std)),
                        float(wrap_angle(bearing + rng.normal(0.0, b_std))),
                    )
                )
        observations.append(step_obs)
    return observations


def build_demo_data(config: dict) -> dict:
    rng = np.random.default_rng(int(config["random_seed"]))
    landmarks = np.array(config["landmarks"], dtype=float)
    true_trajectory = make_true_trajectory(config)
    true_controls = controls_from_trajectory(true_trajectory, float(config["dt"]))
    odom_trajectory, odom_controls = make_odometry(config, true_controls, true_trajectory[0], rng)
    observations = make_observations(config, true_trajectory, landmarks, rng)
    return {
        "landmarks": landmarks,
        "true_trajectory": true_trajectory,
        "true_controls": true_controls,
        "odom_trajectory": odom_trajectory,
        "odom_controls": odom_controls,
        "observations": observations,
    }


def initialize_particles(
    config: dict,
    rng: np.random.Generator,
    initial_pose: np.ndarray | None = None,
) -> np.ndarray:
    n = int(config["num_particles"])
    width, height = [float(v) for v in config["map_size"]]
    particles = np.zeros((n, 3), dtype=float)

    if initial_pose is None:
        particles[:, 0] = rng.uniform(0.0, width, size=n)
        particles[:, 1] = rng.uniform(0.0, height, size=n)
        particles[:, 2] = rng.uniform(-math.pi, math.pi, size=n)
        return particles

    init = config.get("initialization", {})
    position_std = float(init.get("position_std", 0.45))
    theta_std = float(init.get("theta_std", 0.35))
    global_fraction = float(init.get("global_fraction", 0.15))
    global_count = int(np.clip(round(n * global_fraction), 0, n))
    local_count = n - global_count

    particles[:local_count, 0] = initial_pose[0] + rng.normal(0.0, position_std, size=local_count)
    particles[:local_count, 1] = initial_pose[1] + rng.normal(0.0, position_std, size=local_count)
    particles[:local_count, 2] = wrap_angle(initial_pose[2] + rng.normal(0.0, theta_std, size=local_count))

    if global_count > 0:
        particles[local_count:, 0] = rng.uniform(0.0, width, size=global_count)
        particles[local_count:, 1] = rng.uniform(0.0, height, size=global_count)
        particles[local_count:, 2] = rng.uniform(-math.pi, math.pi, size=global_count)

    particles[:, 0] = np.clip(particles[:, 0], 0.0, width)
    particles[:, 1] = np.clip(particles[:, 1], 0.0, height)
    return particles


def predict_particles(
    particles: np.ndarray,
    control: np.ndarray,
    config: dict,
    rng: np.random.Generator,
) -> np.ndarray:
    n = len(particles)
    dt = float(config["dt"])
    noise = config["motion_noise"]
    controls = np.zeros((n, 2), dtype=float)
    controls[:, 0] = control[0] + rng.normal(0.0, float(noise["v_std"]), size=n)
    controls[:, 1] = control[1] + rng.normal(0.0, float(noise["w_std"]), size=n)
    return motion_model_batch(particles, controls, dt)


def compute_particle_weights(
    particles: np.ndarray,
    observations: list[tuple[int, float, float]],
    landmarks: np.ndarray,
    config: dict,
) -> np.ndarray:
    n = len(particles)
    if not observations:
        return np.full(n, 1.0 / n, dtype=float)

    r_std = float(config["observation_noise"]["range_std"])
    b_std = float(config["observation_noise"]["bearing_std"])
    log_w = np.zeros(n, dtype=float)

    for landmark_id, observed_range, observed_bearing in observations:
        landmark = landmarks[landmark_id]
        dx = landmark[0] - particles[:, 0]
        dy = landmark[1] - particles[:, 1]
        pred_range = np.hypot(dx, dy)
        pred_bearing = wrap_angle(np.arctan2(dy, dx) - particles[:, 2])

        range_error = observed_range - pred_range
        bearing_error = wrap_angle(observed_bearing - pred_bearing)
        log_w += -0.5 * ((range_error / r_std) ** 2 + (bearing_error / b_std) ** 2)

    log_w -= np.max(log_w)
    weights = np.exp(log_w)
    total = np.sum(weights)
    if not np.isfinite(total) or total <= 0.0:
        return np.full(n, 1.0 / n, dtype=float)
    return weights / total


def systematic_resample(
    particles: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(particles)
    positions = (rng.random() + np.arange(n)) / n
    cumulative = np.cumsum(weights)
    cumulative[-1] = 1.0
    indexes = np.searchsorted(cumulative, positions)
    resampled = particles[indexes].copy()
    new_weights = np.full(n, 1.0 / n, dtype=float)
    return resampled, new_weights


def estimate_pose(particles: np.ndarray, weights: np.ndarray) -> np.ndarray:
    x = np.average(particles[:, 0], weights=weights)
    y = np.average(particles[:, 1], weights=weights)
    sin_sum = np.average(np.sin(particles[:, 2]), weights=weights)
    cos_sum = np.average(np.cos(particles[:, 2]), weights=weights)
    theta = math.atan2(sin_sum, cos_sum)
    return np.array([x, y, theta], dtype=float)


def run_particle_filter(config: dict) -> dict:
    data = build_demo_data(config)
    rng = np.random.default_rng(int(config["random_seed"]) + 100)
    particles = initialize_particles(config, rng, data["true_trajectory"][0])
    weights = np.full(len(particles), 1.0 / len(particles), dtype=float)

    estimated = [estimate_pose(particles, weights)]
    particle_snapshots = [particles.copy()]
    weight_snapshots = [weights.copy()]

    for step, control in enumerate(data["odom_controls"], start=1):
        particles = predict_particles(particles, control, config, rng)
        weights = compute_particle_weights(
            particles,
            data["observations"][step],
            data["landmarks"],
            config,
        )
        estimated.append(estimate_pose(particles, weights))
        particle_snapshots.append(particles.copy())
        weight_snapshots.append(weights.copy())
        particles, weights = systematic_resample(particles, weights, rng)

    data["estimated_trajectory"] = np.array(estimated)
    data["particle_snapshots"] = particle_snapshots
    data["weight_snapshots"] = weight_snapshots
    return data


def position_errors(reference: np.ndarray, estimate: np.ndarray) -> np.ndarray:
    return np.linalg.norm(reference[:, :2] - estimate[:, :2], axis=1)


def pose_to_text(pose: np.ndarray) -> str:
    return f"x={pose[0]:.3f}, y={pose[1]:.3f}, theta={pose[2]:.3f}"


def metrics_text(data: dict) -> str:
    true = data["true_trajectory"]
    odom = data["odom_trajectory"]
    est = data["estimated_trajectory"]
    odom_errors = position_errors(true, odom)
    pf_errors = position_errors(true, est)

    lines = [
        "Robot localization demo metrics",
        "",
        f"Final true pose:      {pose_to_text(true[-1])}",
        f"Final odometry pose:  {pose_to_text(odom[-1])}",
        f"Final PF pose:        {pose_to_text(est[-1])}",
        "",
        f"Mean odometry error:  {np.mean(odom_errors):.3f} m",
        f"Mean PF error:        {np.mean(pf_errors):.3f} m",
        f"Final odometry error: {odom_errors[-1]:.3f} m",
        f"Final PF error:       {pf_errors[-1]:.3f} m",
    ]
    return "\n".join(lines)


def ensure_output_dir(path: str | Path | None = None) -> Path:
    output_dir = Path(path) if path else ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
