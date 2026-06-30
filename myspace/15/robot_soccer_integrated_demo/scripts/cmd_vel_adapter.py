#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rospy
from gazebo_msgs.msg import ModelState, ModelStates
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

from ikwalk_engine import IKWalkEngine, IKWalkParameters, angles_to_ros_command


def _clamp(value, low, high):
    return max(low, min(high, value))


def _yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def _quaternion_from_yaw(yaw):
    q = ModelState().pose.orientation
    q.z = math.sin(0.5 * yaw)
    q.w = math.cos(0.5 * yaw)
    return q


class CmdVelAdapter:
    def __init__(self):
        rospy.init_node("cmd_vel_adapter")

        self.IKWalkParameters = IKWalkParameters
        self.angles_to_ros_command = angles_to_ros_command
        self.engine = IKWalkEngine()

        self.rate_hz = rospy.get_param("~rate_hz", 50.0)
        self.cmd_timeout = rospy.get_param("~cmd_timeout", 0.5)
        self.max_linear_x = max(rospy.get_param("~max_linear_x", 0.20), 1e-6)
        self.max_linear_y = max(rospy.get_param("~max_linear_y", 0.08), 1e-6)
        self.max_angular_z = max(rospy.get_param("~max_angular_z", 0.8), 1e-6)

        self.step_gain = rospy.get_param("~step_gain", 0.020)
        self.lateral_gain = rospy.get_param("~lateral_gain", 0.018)
        self.turn_gain = rospy.get_param("~turn_gain", 0.20)
        self.rise_gain = rospy.get_param("~rise_gain", 0.035)
        self.swing_gain = rospy.get_param("~swing_gain", 0.020)
        self.trunk_pitch = rospy.get_param("~trunk_pitch", 0.05)
        self.trunk_z_offset = rospy.get_param("~trunk_z_offset", 0.02)
        self.drive_model_state = rospy.get_param("~drive_model_state", True)
        self.hold_model_upright = rospy.get_param("~hold_model_upright", True)
        self.robot_model = rospy.get_param("~robot_model", "robot1")
        self.base_z = rospy.get_param("~base_z", 0.01)

        cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "cmd_vel")
        command_topic = rospy.get_param(
            "~command_topic", "/humanoid/position_controller/command"
        )

        self.latest_cmd = Twist()
        self.latest_cmd_time = rospy.Time(0)
        self.latest_pose = None
        self.pub = rospy.Publisher(command_topic, Float64MultiArray, queue_size=10)
        self.model_pub = rospy.Publisher("/gazebo/set_model_state", ModelState, queue_size=10)
        self.sub = rospy.Subscriber(cmd_vel_topic, Twist, self._cmd_callback, queue_size=1)
        self.model_sub = rospy.Subscriber(
            "/gazebo/model_states", ModelStates, self._model_states_callback, queue_size=1
        )

        rospy.loginfo(
            "cmd_vel_adapter: %s -> %s",
            rospy.resolve_name(cmd_vel_topic),
            rospy.resolve_name(command_topic),
        )

    def _cmd_callback(self, msg):
        self.latest_cmd = msg
        self.latest_cmd_time = rospy.Time.now()

    def _model_states_callback(self, msg):
        try:
            index = msg.name.index(self.robot_model)
        except ValueError:
            return
        self.latest_pose = msg.pose[index]

    def _fresh_cmd(self):
        if self.latest_cmd_time == rospy.Time(0):
            return None
        if (rospy.Time.now() - self.latest_cmd_time).to_sec() > self.cmd_timeout:
            return None
        return self.latest_cmd

    def _build_params(self, cmd):
        params = self.IKWalkParameters()
        params.riseGain = self.rise_gain
        params.swingGain = self.swing_gain
        params.trunkPitch = self.trunk_pitch
        params.trunkZOffset = self.trunk_z_offset

        if cmd is None:
            params.enabledGain = 0.0
            return params

        vx = _clamp(cmd.linear.x / self.max_linear_x, -1.0, 1.0)
        vy = _clamp(cmd.linear.y / self.max_linear_y, -1.0, 1.0)
        wz = _clamp(cmd.angular.z / self.max_angular_z, -1.0, 1.0)

        # IKWalk's positive foot X convention moves this Gazebo model backward.
        # Keep ROS cmd_vel semantics: positive linear.x means robot forward.
        params.stepGain = -vx * self.step_gain
        params.lateralGain = vy * self.lateral_gain
        params.turnGain = wz * self.turn_gain
        moving = math.fabs(vx) + math.fabs(vy) + math.fabs(wz) > 0.03
        params.enabledGain = 1.0 if moving else 0.0
        return params

    def _publish_model_state(self, cmd, dt):
        if not self.drive_model_state or self.latest_pose is None:
            return

        pose = self.latest_pose
        yaw = _yaw_from_quaternion(pose.orientation)
        x = pose.position.x
        y = pose.position.y

        if cmd is not None:
            linear_x = _clamp(cmd.linear.x, -self.max_linear_x, self.max_linear_x)
            linear_y = _clamp(cmd.linear.y, -self.max_linear_y, self.max_linear_y)
            angular_z = _clamp(cmd.angular.z, -self.max_angular_z, self.max_angular_z)
            x += (math.cos(yaw) * linear_x - math.sin(yaw) * linear_y) * dt
            y += (math.sin(yaw) * linear_x + math.cos(yaw) * linear_y) * dt
            yaw += angular_z * dt
        elif not self.hold_model_upright:
            return

        state = ModelState()
        state.model_name = self.robot_model
        state.reference_frame = "world"
        state.pose.position.x = x
        state.pose.position.y = y
        state.pose.position.z = self.base_z
        state.pose.orientation = _quaternion_from_yaw(yaw)
        self.model_pub.publish(state)

    def _publish_zero_pose(self):
        outputs = self.engine.get_zero_pose()
        msg = Float64MultiArray()
        msg.data = self.angles_to_ros_command(outputs)
        self.pub.publish(msg)

    def run(self):
        dt = 1.0 / self.rate_hz
        rate = rospy.Rate(self.rate_hz)

        for _ in range(30):
            if rospy.is_shutdown():
                return
            self._publish_zero_pose()
            rate.sleep()

        while not rospy.is_shutdown():
            cmd = self._fresh_cmd()
            params = self._build_params(cmd)
            self._publish_model_state(cmd, dt)

            if params.enabledGain <= 0.0:
                self._publish_zero_pose()
            else:
                result = self.engine.compute(dt, params)
                if result is None:
                    rospy.logwarn_throttle(1.0, "IKWalk failed; publishing zero pose")
                    self._publish_zero_pose()
                else:
                    msg = Float64MultiArray()
                    msg.data = self.angles_to_ros_command(result)
                    self.pub.publish(msg)

            try:
                rate.sleep()
            except rospy.exceptions.ROSTimeMovedBackwardsException:
                self.engine.phase = 0.0

        for _ in range(20):
            self._publish_zero_pose()


if __name__ == "__main__":
    try:
        CmdVelAdapter().run()
    except rospy.ROSInterruptException:
        pass
