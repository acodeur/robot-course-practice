from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.decision_types import (
    KICK_BALL,
    MOVE_TO_BALL,
    MOVE_TO_SHOOT_POSE,
    ROTATE_SEARCH,
    STOP_AND_RECOVER,
    TURN_TO_GOAL,
    angle_diff_deg,
    clamp,
    distance,
    wrap_angle_deg,
)


FIELD_BG = (232, 244, 235)
FIELD_LINE = (120, 165, 135)
BLUE = (37, 117, 190)
BLUE_DARK = (25, 78, 124)
GREEN = (103, 169, 66)
RED = (204, 0, 0)
GRAY = (105, 116, 128)
LIGHT_GRAY = (241, 244, 247)
BLACK = (30, 35, 42)
WHITE = (255, 255, 255)
ORANGE = (242, 143, 44)
PURPLE = (126, 87, 194)
TEAL = (0, 137, 123)
YELLOW = (230, 166, 35)


STATE_STYLES = {
    "SEARCH_BALL": ((90, 112, 130), "Search ball"),
    "APPROACH_BALL": (BLUE, "Approach ball"),
    "GET_BEHIND_BALL": (TEAL, "Get behind ball"),
    "ALIGN_TO_GOAL": (PURPLE, "Align to goal"),
    "KICK": (ORANGE, "Kick and wait"),
    "LOST_RECOVER": (RED, "Lost recovery"),
}

COMMAND_HINTS = {
    "ROTATE_SEARCH": "Rotate search",
    "MOVE_TO_BALL": "Move to ball",
    "MOVE_TO_SHOOT_POSE": "Move to shoot pose",
    "TURN_TO_GOAL": "Turn only",
    "KICK_BALL": "Kick ball",
    "STOP_AND_RECOVER": "Stop and recover",
}


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class DecisionSimulator:
    def __init__(self, config: Dict, agent, root_dir: Path):
        self.config = config
        self.agent = agent
        self.root_dir = root_dir
        self.outputs_dir = root_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.rng = random.Random(config["random_seed"])
        self.reset()

    def reset(self):
        self.dt = self.config["dt"]
        self.step_count = 0
        self.time_s = 0.0
        self.score = 0
        self.last_goal_time = None
        self.kick_count = 0
        self.last_shot_angle_error = None
        self.kick_cooldown = 0
        self.forced_dropout_frames = 0
        self.lost_frames = 0
        self.ball_index = -1
        self._reset_robot_pose()
        x, y = self.robot["x"], self.robot["y"]
        self.robot_trail: List[Tuple[float, float]] = [(x, y)]
        self.state_history: List[Tuple[float, str]] = []
        self.event_log: List[str] = []
        self.current_obs: Dict = {}
        self.current_decision = {"mode": "SEARCH_BALL", "command": "ROTATE_SEARCH", "reason": "initial state"}
        self.phase_pause_frames_remaining = 0
        self.phase_pause_total_frames = self._phase_pause_total_frames()
        self.phase_pause_mode = ""
        self.spawn_next_ball()
        self.agent.reset(self.config)
        self.log_event("reset scenario")

    def _phase_pause_total_frames(self) -> int:
        ui_cfg = self.config.get("ui", {})
        seconds = max(0.0, float(ui_cfg.get("phase_pause_seconds", 0.0)))
        fps = max(1, int(ui_cfg.get("fps", 60)))
        return int(round(seconds * fps))

    def _reset_robot_pose(self):
        x, y, theta = self.config["robot"]["start_pose"]
        self.robot = {"x": x, "y": y, "theta": theta}

    def spawn_next_ball(self, reset_robot: bool = False, reset_agent: bool = False):
        positions = self.config["scenario"]["ball_positions"]
        self.ball_index = (self.ball_index + 1) % len(positions)
        bx, by = positions[self.ball_index]
        self.ball = {"x": bx, "y": by, "vx": 0.0, "vy": 0.0, "roll_distance": 0.0}
        self.kick_cooldown = 0
        self.phase_pause_frames_remaining = 0
        self.phase_pause_mode = ""
        if reset_robot:
            self._reset_robot_pose()
            self.robot_trail = [(self.robot["x"], self.robot["y"])]
        if reset_agent:
            self.agent.reset(self.config)
            self.current_decision = {"mode": "SEARCH_BALL", "command": "ROTATE_SEARCH", "reason": "new penalty setup"}

    def manual_dropout(self):
        self.forced_dropout_frames = self.config["perception"]["manual_dropout_frames"]
        self.log_event("manual target loss")

    def log_event(self, message: str):
        line = f"{self.time_s:5.1f}s  {message}"
        self.event_log.append(line)
        self.event_log = self.event_log[-7:]

    def _angle_to(self, target: Tuple[float, float]) -> float:
        dx = target[0] - self.robot["x"]
        dy = target[1] - self.robot["y"]
        return math.degrees(math.atan2(dy, dx))

    def _angle_between(self, start: Tuple[float, float], target: Tuple[float, float]) -> float:
        dx = target[0] - start[0]
        dy = target[1] - start[1]
        return math.degrees(math.atan2(dy, dx))

    def _goal_center(self) -> Tuple[float, float]:
        return (self.config["field"]["goal_x_m"], 0.0)

    def _ball_to_goal_angle(self) -> float:
        return self._angle_between((self.ball["x"], self.ball["y"]), self._goal_center())

    def _shoot_pose(self) -> Tuple[float, float]:
        goal = self._goal_center()
        ball = (self.ball["x"], self.ball["y"])
        dx = goal[0] - ball[0]
        dy = goal[1] - ball[1]
        length = max(0.001, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        distance_m = self.config["decision"]["shoot_pose_distance_m"]
        return (ball[0] - ux * distance_m, ball[1] - uy * distance_m)

    def _ball_speed(self) -> float:
        return math.hypot(self.ball.get("vx", 0.0), self.ball.get("vy", 0.0))

    def observe(self) -> Dict:
        perception = self.config["perception"]
        decision_cfg = self.config["decision"]
        ball_cfg = self.config["ball"]
        ball_xy = (self.ball["x"], self.ball["y"])
        robot_xy = (self.robot["x"], self.robot["y"])
        ball_distance = distance(robot_xy, ball_xy)
        ball_angle_abs = self._angle_to(ball_xy)
        ball_angle = angle_diff_deg(ball_angle_abs, self.robot["theta"])
        goal_angle_abs = self._angle_to(self._goal_center())
        robot_to_goal_angle = angle_diff_deg(goal_angle_abs, self.robot["theta"])
        ball_to_goal_angle = self._ball_to_goal_angle()
        shot_angle_error = angle_diff_deg(ball_to_goal_angle, self.robot["theta"])
        shoot_pose = self._shoot_pose()
        shoot_pose_distance = distance(robot_xy, shoot_pose)
        ball_is_moving = self._ball_speed() > ball_cfg["stop_speed_mps"]
        kick_ready = (
            (not ball_is_moving)
            and ball_distance <= decision_cfg["kick_distance_m"]
            and shoot_pose_distance <= decision_cfg["shoot_pose_tolerance_m"]
            and abs(shot_angle_error) <= decision_cfg["align_angle_threshold_deg"]
        )

        in_range = ball_distance <= perception["sensor_range_m"]
        in_fov = abs(ball_angle) <= perception["fov_deg"] / 2.0
        random_dropout = self.rng.random() < perception["dropout_probability"]
        forced_dropout = self.forced_dropout_frames > 0
        if self.forced_dropout_frames > 0:
            self.forced_dropout_frames -= 1

        visible = in_range and in_fov and (not random_dropout) and (not forced_dropout)
        if visible:
            confidence = 1.0
            confidence -= 0.30 * (ball_distance / perception["sensor_range_m"])
            confidence -= 0.22 * (abs(ball_angle) / max(1.0, perception["fov_deg"] / 2.0))
            confidence += self.rng.gauss(0.0, perception["noise_std"])
            confidence = clamp(confidence, 0.0, 1.0)
            self.lost_frames = 0
        else:
            confidence = 0.0
            self.lost_frames += 1

        obs = {
            "time_s": self.time_s,
            "ball_visible": visible,
            "ball_confidence": confidence,
            "ball_distance": ball_distance,
            "ball_angle_deg": ball_angle,
            "goal_angle_deg": shot_angle_error,
            "robot_to_goal_angle_deg": robot_to_goal_angle,
            "ball_to_goal_angle_deg": ball_to_goal_angle,
            "shot_angle_error_deg": shot_angle_error,
            "shoot_pose": shoot_pose,
            "shoot_pose_distance": shoot_pose_distance,
            "ball_is_moving": ball_is_moving,
            "kick_ready": kick_ready,
            "robot_pose": (self.robot["x"], self.robot["y"], self.robot["theta"]),
            "lost_frames": self.lost_frames,
            "score": self.score,
        }
        self.current_obs = obs
        return obs

    def step(self):
        if self.phase_pause_frames_remaining > 0:
            self.phase_pause_frames_remaining -= 1
            self.step_count += 1
            self.time_s += self.dt
            return

        obs = self.observe()
        decision = self.agent.decide(obs)
        self.current_decision = decision
        mode_changed = not self.state_history or self.state_history[-1][1] != decision["mode"]
        if mode_changed:
            self.state_history.append((self.time_s, decision["mode"]))
            self.state_history = self.state_history[-16:]
            self.log_event(f"state -> {decision['mode']}: {decision['reason']}")
            if self.phase_pause_total_frames > 0:
                self.phase_pause_frames_remaining = self.phase_pause_total_frames
                self.phase_pause_mode = decision["mode"]
                self.step_count += 1
                self.time_s += self.dt
                return

        self.apply_command(decision["command"])
        self._update_ball()
        if self.kick_cooldown > 0:
            self.kick_cooldown -= 1
        self.step_count += 1
        self.time_s += self.dt
        self.robot_trail.append((self.robot["x"], self.robot["y"]))
        self.robot_trail = self.robot_trail[-360:]

    def apply_command(self, command: str):
        robot_cfg = self.config["robot"]
        field_cfg = self.config["field"]
        decision_cfg = self.config["decision"]

        if command == ROTATE_SEARCH:
            self.robot["theta"] = wrap_angle_deg(
                self.robot["theta"] + robot_cfg["search_turn_degps"] * self.dt
            )
            return

        if command == MOVE_TO_BALL:
            target_angle = self._angle_to((self.ball["x"], self.ball["y"]))
            self._turn_toward(target_angle)
            if abs(angle_diff_deg(target_angle, self.robot["theta"])) < 65.0:
                self._move_forward(robot_cfg["move_speed_mps"] * self.dt)
            return

        if command == MOVE_TO_SHOOT_POSE:
            self._move_to_point(self._shoot_pose())
            return

        if command == TURN_TO_GOAL:
            self._turn_toward(self._ball_to_goal_angle())
            return

        if command == KICK_BALL:
            if self.kick_cooldown > 0 or self.current_obs.get("ball_is_moving", False):
                return
            if self.current_obs.get("kick_ready", False):
                ball_cfg = self.config["ball"]
                angle_noise = self.rng.gauss(0.0, ball_cfg["kick_angle_noise_deg"])
                speed_noise = self.rng.gauss(0.0, ball_cfg["kick_speed_noise_ratio"])
                kick_angle = math.radians(wrap_angle_deg(self.robot["theta"] + angle_noise))
                kick_speed = max(0.0, ball_cfg["kick_speed_mps"] * (1.0 + speed_noise))
                self.ball["vx"] = math.cos(kick_angle) * kick_speed
                self.ball["vy"] = math.sin(kick_angle) * kick_speed
                self.ball["roll_distance"] = 0.0
                self.kick_count += 1
                self.kick_cooldown = decision_cfg["kick_cooldown_frames"]
                self.last_shot_angle_error = self.current_obs.get("shot_angle_error_deg")
                self.log_event(f"kick! error={self.last_shot_angle_error:.1f} deg")
            return

        if command == STOP_AND_RECOVER:
            self.robot["theta"] = wrap_angle_deg(self.robot["theta"] + 0.25 * robot_cfg["search_turn_degps"] * self.dt)

    def _turn_toward(self, target_angle: float):
        turn_limit = self.config["robot"]["turn_speed_degps"] * self.dt
        err = angle_diff_deg(target_angle, self.robot["theta"])
        self.robot["theta"] = wrap_angle_deg(self.robot["theta"] + clamp(err, -turn_limit, turn_limit))

    def _move_to_point(self, target: Tuple[float, float]):
        target_angle = self._angle_to(target)
        self._turn_toward(target_angle)
        if abs(angle_diff_deg(target_angle, self.robot["theta"])) < 55.0:
            remaining = distance((self.robot["x"], self.robot["y"]), target)
            step = min(self.config["robot"]["move_speed_mps"] * self.dt, remaining)
            self._move_forward(step)

    def _move_forward(self, distance_m: float):
        field = self.config["field"]
        theta = math.radians(self.robot["theta"])
        self.robot["x"] += math.cos(theta) * distance_m
        self.robot["y"] += math.sin(theta) * distance_m
        self.robot["x"] = clamp(self.robot["x"], -field["width_m"] / 2.0 + 0.2, field["width_m"] / 2.0 - 0.2)
        self.robot["y"] = clamp(self.robot["y"], -field["height_m"] / 2.0 + 0.2, field["height_m"] / 2.0 - 0.2)

    def _update_ball(self):
        speed = self._ball_speed()
        ball_cfg = self.config["ball"]
        if speed <= ball_cfg["stop_speed_mps"]:
            self.ball["vx"] = 0.0
            self.ball["vy"] = 0.0
            return

        old_x, old_y = self.ball["x"], self.ball["y"]
        new_x = old_x + self.ball["vx"] * self.dt
        new_y = old_y + self.ball["vy"] * self.dt
        if self._crossed_goal(old_x, old_y, new_x, new_y):
            self._register_goal()
            return

        self.ball["x"] = new_x
        self.ball["y"] = new_y
        self.ball["roll_distance"] += distance((old_x, old_y), (new_x, new_y))

        field = self.config["field"]
        margin = ball_cfg["radius_m"]
        min_x = -field["width_m"] / 2.0 + margin
        max_x = field["width_m"] / 2.0 - margin
        min_y = -field["height_m"] / 2.0 + margin
        max_y = field["height_m"] / 2.0 - margin
        if not (min_x <= self.ball["x"] <= max_x and min_y <= self.ball["y"] <= max_y):
            self.ball["x"] = clamp(self.ball["x"], min_x, max_x)
            self.ball["y"] = clamp(self.ball["y"], min_y, max_y)
            self.ball["vx"] = 0.0
            self.ball["vy"] = 0.0
            self.log_event("ball stopped at boundary")
            return

        if self.ball["roll_distance"] >= ball_cfg["max_roll_distance_m"]:
            self.ball["vx"] = 0.0
            self.ball["vy"] = 0.0
            self.log_event("ball roll limit reached")
            return

        next_speed = max(0.0, speed - ball_cfg["ball_friction_mps2"] * self.dt)
        if next_speed <= ball_cfg["stop_speed_mps"]:
            self.ball["vx"] = 0.0
            self.ball["vy"] = 0.0
            return
        scale = next_speed / speed
        self.ball["vx"] *= scale
        self.ball["vy"] *= scale

    def _crossed_goal(self, old_x: float, old_y: float, new_x: float, new_y: float) -> bool:
        goal_x = self.config["field"]["goal_x_m"]
        if old_x > goal_x or new_x < goal_x or new_x == old_x:
            return False
        t = (goal_x - old_x) / (new_x - old_x)
        if t < 0.0 or t > 1.0:
            return False
        y_at_goal = old_y + (new_y - old_y) * t
        return abs(y_at_goal) <= self.config["field"]["goal_width_m"] / 2.0

    def _register_goal(self):
        self.score += 1
        self.last_goal_time = self.time_s
        self.ball["vx"] = 0.0
        self.ball["vy"] = 0.0
        self.log_event(f"goal! score={self.score}, time={self.time_s:.1f}s")
        if self.config["scenario"]["reset_after_goal"]:
            self.spawn_next_ball(reset_robot=True, reset_agent=True)
            self.log_event("next penalty setup")

    def write_metrics(self):
        path = self.outputs_dir / "metrics.txt"
        lines = [
            "robot_decision_fsm_demo metrics",
            f"agent_state: {self.current_decision.get('mode', '')}",
            f"last_command: {self.current_decision.get('command', '')}",
            f"score: {self.score}",
            f"kick_count: {self.kick_count}",
            f"last_shot_angle_error_deg: {self.last_shot_angle_error if self.last_shot_angle_error is not None else 'none'}",
            f"last_goal_time: {self.last_goal_time if self.last_goal_time is not None else 'none'}",
            f"sim_time: {self.time_s:.2f}",
            f"robot_pose: x={self.robot['x']:.3f}, y={self.robot['y']:.3f}, theta={self.robot['theta']:.1f}",
            f"ball_position: x={self.ball['x']:.3f}, y={self.ball['y']:.3f}",
            f"ball_speed: {self._ball_speed():.3f}",
            "recent_events:",
            *[f"  {event}" for event in self.event_log],
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


class PygameRenderer:
    def __init__(self, sim: DecisionSimulator):
        try:
            import pygame
        except Exception as exc:
            raise RuntimeError("pygame is not installed. Please run: pip install -r requirements.txt") from exc

        self.pygame = pygame
        pygame.init()
        ui_cfg = sim.config["ui"]
        self.screen_w = ui_cfg["width"]
        self.screen_h = ui_cfg["height"]
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Robot Decision FSM Demo")
        self.clock = pygame.time.Clock()
        # self.font = pygame.font.SysFont("consolas,arial", 24)
        # self.small = pygame.font.SysFont("consolas,arial", 20)
        # self.tiny = pygame.font.SysFont("consolas,arial", 18)
        # self.large = pygame.font.SysFont("consolas,arial", 34, bold=True)
        font_path = "C:/Windows/Fonts/consola.ttf"
        self.font = pygame.font.Font(font_path, 24)
        self.small = pygame.font.Font(font_path, 20)
        self.tiny = pygame.font.Font(font_path, 18)
        self.large = pygame.font.Font(font_path, 34)
        margin = 42
        timeline_h = 150
        gap = 28
        panel_w = 430
        self.field_rect = pygame.Rect(
            margin,
            margin,
            self.screen_w - margin * 2 - panel_w - gap,
            self.screen_h - margin * 2 - timeline_h - gap,
        )
        self.panel_rect = pygame.Rect(
            self.field_rect.right + gap,
            margin,
            panel_w,
            self.field_rect.height,
        )
        self.timeline_rect = pygame.Rect(
            margin,
            self.field_rect.bottom + gap,
            self.screen_w - margin * 2,
            timeline_h,
        )
        self.sim = sim

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        field = self.sim.config["field"]
        sx = self.field_rect.left + (x + field["width_m"] / 2.0) / field["width_m"] * self.field_rect.width
        sy = self.field_rect.top + (field["height_m"] / 2.0 - y) / field["height_m"] * self.field_rect.height
        return int(sx), int(sy)

    def draw(self):
        pygame = self.pygame
        self.screen.fill(WHITE)
        self._draw_field()
        self._draw_robot_and_ball()
        self._draw_panel()
        self._draw_timeline()
        self._draw_phase_pause()
        pygame.display.flip()

    def save_screenshot(self):
        path = self.sim.outputs_dir / "decision_demo_last_frame.png"
        self.pygame.image.save(self.screen, str(path))
        return path

    def _truncate_text(self, text: str, font, max_width: int) -> str:
        text = str(text)
        if font.size(text)[0] <= max_width:
            return text

        suffix = "..."
        if font.size(suffix)[0] > max_width:
            return ""

        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            candidate = text[:mid].rstrip() + suffix
            if font.size(candidate)[0] <= max_width:
                low = mid
            else:
                high = mid - 1
        return text[:low].rstrip() + suffix

    def _fit_text_lines(self, text: str, font, max_width: int, max_lines: int) -> List[str]:
        words = str(text).split()
        if not words:
            return []

        lines: List[str] = []
        current = ""
        for index, word in enumerate(words):
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = word
            else:
                lines.append(self._truncate_text(word, font, max_width))
                current = ""

            if len(lines) == max_lines:
                lines[-1] = self._truncate_text(lines[-1] + " " + " ".join(words[index:]), font, max_width)
                return lines

        if current:
            lines.append(current)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = self._truncate_text(lines[-1], font, max_width)
        return lines

    def _text(self, text: str, x: int, y: int, color=BLACK, font=None, max_width: int | None = None):
        font = font or self.small
        if max_width is not None:
            text = self._truncate_text(str(text), font, max_width)
        surface = font.render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def _draw_field(self):
        pygame = self.pygame
        pygame.draw.rect(self.screen, FIELD_BG, self.field_rect, border_radius=14)
        pygame.draw.rect(self.screen, FIELD_LINE, self.field_rect, width=2, border_radius=14)
        cx = self.field_rect.centerx
        pygame.draw.line(self.screen, FIELD_LINE, (cx, self.field_rect.top), (cx, self.field_rect.bottom), 1)
        pygame.draw.circle(self.screen, FIELD_LINE, self.field_rect.center, max(58, self.field_rect.height // 8), 1)
        goal_x, goal_y = self.world_to_screen(self.sim.config["field"]["goal_x_m"], 0.0)
        goal_half_h = int(self.field_rect.height * 0.12)
        pygame.draw.rect(self.screen, ORANGE, pygame.Rect(goal_x - 8, goal_y - goal_half_h, 16, goal_half_h * 2), border_radius=4)
        self._text("GOAL", goal_x - 28, goal_y - goal_half_h - 36, ORANGE, self.small)

    def _draw_robot_and_ball(self):
        pygame = self.pygame
        trail = [self.world_to_screen(x, y) for x, y in self.sim.robot_trail[-180:]]
        if len(trail) > 1:
            pygame.draw.lines(self.screen, BLUE, False, trail, 2)

        bx, by = self.world_to_screen(self.sim.ball["x"], self.sim.ball["y"])
        goal_x, goal_y = self.world_to_screen(self.sim.config["field"]["goal_x_m"], 0.0)
        shoot_x, shoot_y = self.world_to_screen(*self.sim._shoot_pose())
        pygame.draw.line(self.screen, (245, 182, 96), (bx, by), (goal_x, goal_y), 3)
        pygame.draw.circle(self.screen, GREEN, (shoot_x, shoot_y), 13, 3)
        pygame.draw.line(self.screen, GREEN, (shoot_x - 12, shoot_y), (shoot_x + 12, shoot_y), 3)
        pygame.draw.line(self.screen, GREEN, (shoot_x, shoot_y - 12), (shoot_x, shoot_y + 12), 3)
        pygame.draw.circle(self.screen, ORANGE, (bx, by), 16)
        pygame.draw.circle(self.screen, RED, (bx, by), 16, 3)

        rx, ry = self.world_to_screen(self.sim.robot["x"], self.sim.robot["y"])
        theta = math.radians(self.sim.robot["theta"])
        front = (rx + int(math.cos(theta) * 34), ry - int(math.sin(theta) * 34))
        left = (rx + int(math.cos(theta + 2.45) * 24), ry - int(math.sin(theta + 2.45) * 24))
        right = (rx + int(math.cos(theta - 2.45) * 24), ry - int(math.sin(theta - 2.45) * 24))
        pygame.draw.polygon(self.screen, BLUE, [front, left, right])
        pygame.draw.circle(self.screen, BLUE_DARK, (rx, ry), 7)

        if self.sim.current_obs.get("ball_visible"):
            pygame.draw.line(self.screen, GREEN, (rx, ry), (bx, by), 2)
        else:
            pygame.draw.line(self.screen, GRAY, (rx, ry), (bx, by), 1)

    def _draw_panel(self):
        pygame = self.pygame
        panel = self.panel_rect
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel, border_radius=12)
        pygame.draw.rect(self.screen, (205, 216, 226), panel, width=2, border_radius=12)
        left = panel.left + 28
        value_x = panel.left + 170
        max_value_w = panel.width - 195
        self._text("Decision Panel", left, panel.top + 24, BLUE_DARK, self.large)

        obs = self.sim.current_obs
        decision = self.sim.current_decision
        state = decision.get("mode", "")
        command = decision.get("command", "")
        state_color, phase_text = STATE_STYLES.get(state, (BLUE_DARK, state))
        command_hint = COMMAND_HINTS.get(command, command)

        state_box = pygame.Rect(left, panel.top + 78, panel.width - 56, 86)
        pygame.draw.rect(self.screen, state_color, state_box, border_radius=10)
        self._text("phase", left + 16, state_box.top + 12, WHITE, self.tiny)
        self._text(phase_text, left + 96, state_box.top + 10, WHITE, self.font, max_width=state_box.width - 110)
        self._text(state, left + 16, state_box.top + 48, WHITE, self.small, max_width=state_box.width - 32)

        command_box = pygame.Rect(left, panel.top + 176, panel.width - 56, 70)
        pygame.draw.rect(self.screen, WHITE, command_box, border_radius=10)
        pygame.draw.rect(self.screen, (215, 224, 233), command_box, width=1, border_radius=10)
        self._text("command", left + 16, command_box.top + 10, GRAY, self.tiny)
        self._text(command_hint, left + 120, command_box.top + 8, BLACK, self.small, max_width=command_box.width - 132)
        self._text(command, left + 16, command_box.top + 38, state_color, self.tiny, max_width=command_box.width - 32)

        rows = [
            ("visible", obs.get("ball_visible", False)),
            ("confidence", f"{obs.get('ball_confidence', 0.0):.2f}"),
            ("ball dist", f"{obs.get('ball_distance', 0.0):.2f} m"),
            ("shoot dist", f"{obs.get('shoot_pose_distance', 0.0):.2f} m"),
            ("shot error", f"{obs.get('shot_angle_error_deg', 0.0):.1f} deg"),
            ("kick ready", obs.get("kick_ready", False)),
            ("ball moving", obs.get("ball_is_moving", False)),
            ("score", self.sim.score),
        ]
        y = panel.top + 270
        for label, value in rows:
            self._text(f"{label:12}", left, y, GRAY, self.small)
            color = GREEN if label in {"kick ready", "score"} else BLACK
            self._text(value, value_x, y, color, self.small, max_width=max_value_w)
            y += 32

        self._text("last goal", left, y + 4, GRAY, self.small)
        last_goal = "none" if self.sim.last_goal_time is None else f"{self.sim.last_goal_time:.1f}s"
        self._text(last_goal, value_x, y + 4, BLACK, self.small, max_width=max_value_w)

        reason_box = pygame.Rect(left, panel.bottom - 142, panel.width - 56, 112)
        pygame.draw.rect(self.screen, WHITE, reason_box, border_radius=8)
        self._text("reason", reason_box.left + 16, reason_box.top + 12, GRAY, self.small)
        reason = decision.get("reason", "")
        for idx, line in enumerate(self._fit_text_lines(reason, self.tiny, reason_box.width - 32, 3)):
            self._text(line, reason_box.left + 16, reason_box.top + 44 + 22 * idx, BLACK, self.tiny)

    def _draw_timeline(self):
        pygame = self.pygame
        base = self.timeline_rect
        pygame.draw.rect(self.screen, LIGHT_GRAY, base, border_radius=10)
        left = base.left + 24
        top = base.top + 18
        timeline_w = int(base.width * 0.58)
        log_x = base.left + timeline_w + 52
        log_width = base.right - log_x - 24
        self._text("State timeline", left, top, BLUE_DARK, self.font)
        self._text("Event log", log_x, top, BLUE_DARK, self.font)

        x = left
        block_y = base.top + 64
        width = 185
        for _, state in self.sim.state_history[-6:]:
            color, phase_text = STATE_STYLES.get(state, (BLUE, state))
            pygame.draw.rect(self.screen, color, pygame.Rect(x, block_y, width, 52), border_radius=8)
            self._text(phase_text, x + 10, block_y + 7, WHITE, self.tiny, max_width=width - 20)
            self._text(state, x + 10, block_y + 29, WHITE, self.tiny, max_width=width - 20)
            x += width + 12
            if x + width > left + timeline_w:
                break

        for idx, line in enumerate(self.sim.event_log[-4:]):
            self._text(line, log_x, base.top + 58 + idx * 24, GRAY, self.tiny, max_width=log_width)

    def _draw_phase_pause(self):
        if self.sim.phase_pause_frames_remaining <= 0:
            return
        pygame = self.pygame
        mode = self.sim.phase_pause_mode or self.sim.current_decision.get("mode", "")
        color, phase_text = STATE_STYLES.get(mode, (BLUE_DARK, mode))
        text = f"Phase pause: {phase_text}"
        font = self.font
        padding_x = 22
        padding_y = 14
        text_w, text_h = font.size(text)
        box = pygame.Rect(
            self.field_rect.centerx - text_w // 2 - padding_x,
            self.field_rect.top + 24,
            text_w + padding_x * 2,
            text_h + padding_y * 2,
        )
        pygame.draw.rect(self.screen, color, box, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, box, width=2, border_radius=12)
        self._text(text, box.left + padding_x, box.top + padding_y, WHITE, font)


def run_headless(sim: DecisionSimulator, steps: int):
    for _ in range(steps):
        sim.step()
    metrics = sim.write_metrics()
    print(f"headless finished: score={sim.score}, metrics={metrics}")


def run_interactive(sim: DecisionSimulator):
    renderer = PygameRenderer(sim)
    pygame = renderer.pygame
    ui_cfg = sim.config["ui"]
    running = True
    paused = False
    speed = int(ui_cfg["initial_speed"])
    last_save = None

    while running and sim.step_count < sim.config["max_steps"]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sim.reset()
                elif event.key == pygame.K_n:
                    sim.spawn_next_ball(reset_robot=True, reset_agent=True)
                    sim.log_event("new ball position")
                elif event.key == pygame.K_d:
                    sim.manual_dropout()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    speed = min(5, speed + 1)
                    sim.log_event(f"speed x{speed}")
                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    speed = max(1, speed - 1)
                    sim.log_event(f"speed x{speed}")

        if not paused:
            steps_this_frame = 1 if sim.phase_pause_frames_remaining > 0 else speed
            for _ in range(steps_this_frame):
                sim.step()
                if sim.phase_pause_frames_remaining > 0:
                    break
        renderer.draw()
        renderer.clock.tick(ui_cfg["fps"])

    last_save = renderer.save_screenshot()
    metrics = sim.write_metrics()
    pygame.quit()
    print(f"saved screenshot: {last_save}")
    print(f"saved metrics: {metrics}")
