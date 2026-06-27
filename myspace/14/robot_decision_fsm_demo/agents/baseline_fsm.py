from __future__ import annotations

from scripts.decision_types import (
    ALIGN_TO_GOAL,
    APPROACH_BALL,
    GET_BEHIND_BALL,
    KICK,
    KICK_BALL,
    LOST_RECOVER,
    MOVE_TO_BALL,
    MOVE_TO_SHOOT_POSE,
    ROTATE_SEARCH,
    SEARCH_BALL,
    STOP_AND_RECOVER,
    TURN_TO_GOAL,
    make_decision,
)


class DecisionAgent:
    """Baseline finite-state machine for the decision demo."""

    def reset(self, config):
        self.state = SEARCH_BALL
        self.kick_timer = 0
        self.recover_timer = 0
        decision_cfg = config["decision"]
        perception_cfg = config["perception"]
        self.conf_threshold = perception_cfg["confidence_threshold"]
        self.approach_distance = decision_cfg["approach_distance_m"]
        self.shoot_pose_tolerance = decision_cfg["shoot_pose_tolerance_m"]
        self.align_threshold = decision_cfg["align_angle_threshold_deg"]
        self.lost_limit = decision_cfg["lost_frame_limit"]
        self.recover_frames = decision_cfg["recover_frames"]
        self.kick_frames = decision_cfg["kick_frames"]

    def decide(self, obs):
        visible = obs["ball_visible"] and obs["ball_confidence"] >= self.conf_threshold
        lost_too_long = obs["lost_frames"] >= self.lost_limit
        ball_moving = obs.get("ball_is_moving", False)

        if self.state == SEARCH_BALL:
            if ball_moving:
                return make_decision(self.state, STOP_AND_RECOVER, "waiting for ball to stop")
            if visible:
                self.state = APPROACH_BALL
                return make_decision(self.state, MOVE_TO_BALL, "ball visible with enough confidence")
            return make_decision(self.state, ROTATE_SEARCH, "searching for ball")

        if self.state == APPROACH_BALL:
            if lost_too_long:
                self.state = LOST_RECOVER
                self.recover_timer = self.recover_frames
                return make_decision(self.state, STOP_AND_RECOVER, "ball lost for too many frames")
            if obs["ball_distance"] <= self.approach_distance:
                self.state = GET_BEHIND_BALL
                return make_decision(self.state, MOVE_TO_SHOOT_POSE, "close enough, move behind ball")
            return make_decision(self.state, MOVE_TO_BALL, "move toward ball")

        if self.state == GET_BEHIND_BALL:
            if ball_moving:
                self.state = SEARCH_BALL
                return make_decision(self.state, STOP_AND_RECOVER, "ball is moving, wait before repositioning")
            if obs["shoot_pose_distance"] <= self.shoot_pose_tolerance:
                self.state = ALIGN_TO_GOAL
                return make_decision(self.state, TURN_TO_GOAL, "at shoot pose, align to ball-goal line")
            return make_decision(self.state, MOVE_TO_SHOOT_POSE, "move behind ball for a clean shot")

        if self.state == ALIGN_TO_GOAL:
            if lost_too_long:
                self.state = LOST_RECOVER
                self.recover_timer = self.recover_frames
                return make_decision(self.state, STOP_AND_RECOVER, "ball lost while aligning")
            if obs["shoot_pose_distance"] > self.shoot_pose_tolerance * 1.8:
                self.state = GET_BEHIND_BALL
                return make_decision(self.state, MOVE_TO_SHOOT_POSE, "left shoot pose, reposition")
            if obs.get("kick_ready", False) and abs(obs["shot_angle_error_deg"]) <= self.align_threshold:
                self.state = KICK
                self.kick_timer = self.kick_frames
                return make_decision(self.state, KICK_BALL, "aligned with ball-goal line")
            return make_decision(self.state, TURN_TO_GOAL, "rotate to ball-goal line")

        if self.state == KICK:
            if self.kick_timer > 0:
                self.kick_timer -= 1
                return make_decision(self.state, KICK_BALL, "kicking")
            if ball_moving:
                return make_decision(self.state, STOP_AND_RECOVER, "shot in progress")
            self.state = SEARCH_BALL
            return make_decision(self.state, ROTATE_SEARCH, "kick finished, search next setup")

        if self.state == LOST_RECOVER:
            if self.recover_timer > 0:
                self.recover_timer -= 1
                return make_decision(self.state, STOP_AND_RECOVER, "recovering after target loss")
            self.state = SEARCH_BALL
            return make_decision(self.state, ROTATE_SEARCH, "recover finished, search again")

        self.state = SEARCH_BALL
        return make_decision(self.state, ROTATE_SEARCH, "unknown state, reset to search")
