#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

import rospy
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import String


def _clamp(value, low, high):
    return max(low, min(high, value))


class SoccerDemoNode:
    SEARCH_BALL = "SEARCH_BALL"
    CENTER_BALL = "CENTER_BALL"
    APPROACH_BALL = "APPROACH_BALL"
    DRIBBLE_BALL = "DRIBBLE_BALL"
    SHOOT = "SHOOT"
    RECOVER = "RECOVER"

    def __init__(self):
        rospy.init_node("soccer_demo_node")

        self.rate_hz = rospy.get_param("~rate_hz", 10.0)
        self.ball_timeout = rospy.get_param("~ball_timeout", 0.7)
        self.search_angular_z = rospy.get_param("~search_angular_z", 0.25)
        self.center_tolerance = rospy.get_param("~center_tolerance", 0.10)
        self.center_gain = rospy.get_param("~center_gain", 0.9)
        self.bearing_gain = rospy.get_param("~bearing_gain", 1.0)
        self.max_turn_speed = rospy.get_param("~max_turn_speed", 0.45)
        self.approach_distance = rospy.get_param("~approach_distance", 0.75)
        self.dribble_distance = rospy.get_param("~dribble_distance", 0.28)
        self.shoot_distance = rospy.get_param("~shoot_distance", 0.18)
        self.approach_speed = rospy.get_param("~approach_speed", 0.08)
        self.dribble_speed = rospy.get_param("~dribble_speed", 0.045)
        self.shoot_speed = rospy.get_param("~shoot_speed", 0.12)
        self.recover_time = rospy.get_param("~recover_time", 1.0)

        self.ball_pose = None
        self.ball_time = rospy.Time(0)
        self.goal_pose = None
        self.goal_time = rospy.Time(0)
        self.last_seen_time = rospy.Time(0)

        self.cmd_pub = rospy.Publisher("cmd_vel", Twist, queue_size=10)
        self.state_pub = rospy.Publisher("decision_state", String, queue_size=10)
        self.ball_sub = rospy.Subscriber(
            "ball_pose", PoseStamped, self._ball_callback, queue_size=1
        )
        self.goal_sub = rospy.Subscriber(
            "goal_pose", PoseStamped, self._goal_callback, queue_size=1
        )

        rospy.loginfo("soccer_demo_node: decision -> cmd_vel")

    def _ball_callback(self, msg):
        self.ball_pose = msg
        self.ball_time = rospy.Time.now()
        self.last_seen_time = self.ball_time

    def _goal_callback(self, msg):
        self.goal_pose = msg
        self.goal_time = rospy.Time.now()

    def _fresh_ball(self):
        if self.ball_pose is None:
            return None
        if (rospy.Time.now() - self.ball_time).to_sec() > self.ball_timeout:
            return None
        return self.ball_pose

    def _fresh_goal(self):
        if self.goal_pose is None:
            return None
        if (rospy.Time.now() - self.goal_time).to_sec() > self.ball_timeout:
            return None
        return self.goal_pose

    def _turn_from_pose(self, pose):
        bearing = math.atan2(pose.pose.position.y, pose.pose.position.x)
        return _clamp(
            self.bearing_gain * bearing, -self.max_turn_speed, self.max_turn_speed
        )

    def _publish(self, state, linear_x=0.0, angular_z=0.0):
        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.angular.z = angular_z
        self.cmd_pub.publish(cmd)
        self.state_pub.publish(String(data=state))

    def _update(self):
        now = rospy.Time.now()
        ball = self._fresh_ball()
        if ball is None:
            if (
                self.last_seen_time != rospy.Time(0)
                and (now - self.last_seen_time).to_sec() < self.recover_time
            ):
                self._publish(self.RECOVER)
            else:
                self._publish(self.SEARCH_BALL, angular_z=self.search_angular_z)
            return

        rel_x = ball.pose.position.x
        rel_y = ball.pose.position.y
        distance = math.hypot(rel_x, rel_y)
        bearing_turn = self._turn_from_pose(ball)

        if rel_x < -0.05:
            turn = self.search_angular_z if rel_y >= 0.0 else -self.search_angular_z
            self._publish(self.SEARCH_BALL, angular_z=turn)
            return

        if distance > self.approach_distance:
            self._publish(self.APPROACH_BALL, self.approach_speed, bearing_turn)
            return

        if distance > self.dribble_distance:
            self._publish(self.DRIBBLE_BALL, self.dribble_speed, 0.6 * bearing_turn)
            return

        goal = self._fresh_goal()
        if goal is not None:
            goal_turn = _clamp(
                0.6 * self._turn_from_pose(goal),
                -self.max_turn_speed,
                self.max_turn_speed,
            )
        else:
            goal_turn = 0.0
        speed = self.shoot_speed if distance <= self.shoot_distance else self.dribble_speed
        self._publish(self.SHOOT, speed, goal_turn)

    def run(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            self._update()
            rate.sleep()


if __name__ == "__main__":
    try:
        SoccerDemoNode().run()
    except rospy.ROSInterruptException:
        pass
