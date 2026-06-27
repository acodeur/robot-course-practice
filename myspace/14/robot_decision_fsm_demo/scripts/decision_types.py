from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple


SEARCH_BALL = "SEARCH_BALL"
APPROACH_BALL = "APPROACH_BALL"
GET_BEHIND_BALL = "GET_BEHIND_BALL"
ALIGN_TO_GOAL = "ALIGN_TO_GOAL"
KICK = "KICK"
LOST_RECOVER = "LOST_RECOVER"

ROTATE_SEARCH = "ROTATE_SEARCH"
MOVE_TO_BALL = "MOVE_TO_BALL"
MOVE_TO_SHOOT_POSE = "MOVE_TO_SHOOT_POSE"
TURN_TO_GOAL = "TURN_TO_GOAL"
KICK_BALL = "KICK_BALL"
STOP_AND_RECOVER = "STOP_AND_RECOVER"

VALID_MODES = {SEARCH_BALL, APPROACH_BALL, GET_BEHIND_BALL, ALIGN_TO_GOAL, KICK, LOST_RECOVER}
VALID_COMMANDS = {
    ROTATE_SEARCH,
    MOVE_TO_BALL,
    MOVE_TO_SHOOT_POSE,
    TURN_TO_GOAL,
    KICK_BALL,
    STOP_AND_RECOVER,
}


@dataclass
class Decision:
    mode: str
    command: str
    reason: str

    def as_dict(self) -> Dict[str, str]:
        return {"mode": self.mode, "command": self.command, "reason": self.reason}


def make_decision(mode: str, command: str, reason: str) -> Dict[str, str]:
    if mode not in VALID_MODES:
        mode = SEARCH_BALL
        reason = "invalid mode -> SEARCH_BALL"
    if command not in VALID_COMMANDS:
        command = ROTATE_SEARCH
        reason = "invalid command -> ROTATE_SEARCH"
    return Decision(mode=mode, command=command, reason=reason).as_dict()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wrap_angle_deg(angle: float) -> float:
    while angle > 180.0:
        angle -= 360.0
    while angle < -180.0:
        angle += 360.0
    return angle


def angle_diff_deg(target: float, current: float) -> float:
    return wrap_angle_deg(target - current)


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
