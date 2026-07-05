#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

import rospy
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import Twist
from std_msgs.msg import String


def _yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _angle_wrap(value):
    return math.atan2(math.sin(value), math.cos(value))


class GoalieNode:
    def __init__(self):
        rospy.init_node("goalie_node")

        self.robot_model = rospy.get_param("~robot_model", "robot2")
        self.ball_model = rospy.get_param("~ball_model", "soccer_ball")
        self.rate_hz = rospy.get_param("~rate_hz", 10.0)
        self.stale_timeout = rospy.get_param("~stale_timeout", 1.0)
        self.home_x = rospy.get_param("~home_x", -3.8)
        self.home_yaw = rospy.get_param("~home_yaw", 0.0)
        self.min_y = rospy.get_param("~min_y", -1.3)
        self.max_y = rospy.get_param("~max_y", 1.3)
        self.y_tolerance = rospy.get_param("~y_tolerance", 0.08)
        self.x_tolerance = rospy.get_param("~x_tolerance", 0.08)
        self.y_gain = rospy.get_param("~y_gain", 0.9)
        self.x_gain = rospy.get_param("~x_gain", 0.5)
        self.yaw_gain = rospy.get_param("~yaw_gain", 1.0)
        self.max_linear_x = rospy.get_param("~max_linear_x", 0.08)
        self.max_linear_y = rospy.get_param("~max_linear_y", 0.08)
        self.max_angular_z = rospy.get_param("~max_angular_z", 0.5)

        self.model_states = None
        self.model_states_time = rospy.Time(0)

        self.cmd_pub = rospy.Publisher("cmd_vel", Twist, queue_size=10)
        self.state_pub = rospy.Publisher("goalie_state", String, queue_size=10)
        self.sub = rospy.Subscriber(
            "/gazebo/model_states", ModelStates, self._states_callback, queue_size=1
        )

        rospy.loginfo("goalie_node: robot=%s ball=%s", self.robot_model, self.ball_model)

    def _states_callback(self, msg):
        self.model_states = msg
        self.model_states_time = rospy.Time.now()

    def _get_pose(self, model_name):
        if self.model_states is None:
            return None
        try:
            index = self.model_states.name.index(model_name)
        except ValueError:
            return None
        return self.model_states.pose[index]

    def _publish(self, state, linear_x=0.0, linear_y=0.0, angular_z=0.0):
        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.linear.y = linear_y
        cmd.angular.z = angular_z
        self.cmd_pub.publish(cmd)
        self.state_pub.publish(String(data=state))

    def _update(self):
        now = rospy.Time.now()
        if (
            self.model_states is None
            or (now - self.model_states_time).to_sec() > self.stale_timeout
        ):
            self._publish("WAIT_MODEL_STATES")
            return

        robot_pose = self._get_pose(self.robot_model)
        ball_pose = self._get_pose(self.ball_model)
        if robot_pose is None or ball_pose is None:
            self._publish("WAIT_MODELS")
            return

        target_y = _clamp(ball_pose.position.y, self.min_y, self.max_y)
        error_y = target_y - robot_pose.position.y
        error_x = self.home_x - robot_pose.position.x
        yaw = _yaw_from_quaternion(robot_pose.orientation)
        yaw_error = _angle_wrap(self.home_yaw - yaw)

        linear_y = 0.0 if abs(error_y) < self.y_tolerance else _clamp(self.y_gain * error_y, -self.max_linear_y, self.max_linear_y)
        linear_x = 0.0 if abs(error_x) < self.x_tolerance else _clamp(self.x_gain * error_x, -self.max_linear_x, self.max_linear_x)
        angular_z = _clamp(self.yaw_gain * yaw_error, -self.max_angular_z, self.max_angular_z)

        state = "HOLD_GOAL" if linear_x == 0.0 and linear_y == 0.0 else "TRACK_BALL_Y"
        self._publish(state, linear_x, linear_y, angular_z)

    def run(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            self._update()
            rate.sleep()


if __name__ == "__main__":
    try:
        GoalieNode().run()
    except rospy.ROSInterruptException:
        pass
