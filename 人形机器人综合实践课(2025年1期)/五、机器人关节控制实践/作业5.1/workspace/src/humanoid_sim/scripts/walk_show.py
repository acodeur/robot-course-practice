#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walk show motion for the humanoid robot.

Features:
- One built-in Walk motion

Usage:
  roslaunch humanoid_sim humanoid_control.launch
    rosrun humanoid_sim walk_show.py
"""

import rospy
from std_msgs.msg import Float64MultiArray


JOINT_ORDER = [
    "left_shoulder_pitch",
    "right_shoulder_pitch",
    "left_elbow",
    "right_elbow",
    "left_hip_pitch",
    "right_hip_pitch",
    "left_knee",
    "right_knee",
]


class WalkShow:
    def __init__(self):

        self.index = {name: i for i, name in enumerate(JOINT_ORDER)}
        self.command = [0.0] * len(JOINT_ORDER)
        # 髋膝联动系数（用于调整质心，防止机器人摔倒）
        self.hip_scale = 2.0

        self.pub = rospy.Publisher(
            "/humanoid/position_controller/command",
            Float64MultiArray,
            queue_size=10,
        )

        rospy.sleep(1.0)
        rospy.loginfo("WalkShow ready")

    def _set_hip_knee(self):
        l_knee = self.command[self.index["left_knee"]]
        r_knee = self.command[self.index["right_knee"]]
        # 髋关节随膝关节运动（抬腿时髋关节前屈）
        self.command[self.index["left_hip_pitch"]] = (-1) * self.hip_scale * l_knee
        self.command[self.index["right_hip_pitch"]] = (-1) * self.hip_scale * r_knee

    def _publish(self):
        self._set_hip_knee()
        self.pub.publish(Float64MultiArray(data=self.command))

    # 再添加左右膝参数
    def walk(self, l_shoulder, r_shoulder, l_elbow, r_elbow, l_knee, r_knee, duration=0.8, rate_hz=30.0):
        duration = max(0.05, duration)
        rate_hz = max(10.0, rate_hz)

        target = list(self.command)
        target[self.index["left_shoulder_pitch"]] = l_shoulder
        target[self.index["right_shoulder_pitch"]] = r_shoulder
        target[self.index["left_elbow"]] = l_elbow
        target[self.index["right_elbow"]] = r_elbow
        target[self.index["left_knee"]] = l_knee
        target[self.index["right_knee"]] = r_knee

        steps = max(1, int(duration * rate_hz))
        start = list(self.command)
        rate = rospy.Rate(rate_hz)

        for step in range(1, steps + 1):
            alpha = float(step) / float(steps)
            for i in range(len(self.command)):
                self.command[i] = start[i] + alpha * (target[i] - start[i])
            self._publish()
            rate.sleep()

    def home(self, duration=1.0):
        self.walk(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, duration=duration)

    def run_show(self):
        rospy.loginfo("Walk show")
        self.home(duration=1.0)

        sequence = [
            # (left_shoulder, right_shoulder, left_elbow, right_elbow, left_knee, right_knee, duration)
            # 左前
            (-0.05, 0.05, -0.05, -0.05, 0.05, 0.0, 0.8),
            (-0.08, 0.08, -0.1, -0.1, 0.10, 0.0, 0.8),
            (-0.1, 0.1, -0.15, -0.15, 0.12, 0.0, 0.8),
            (-0.08, 0.08, -0.1, -0.1, 0.10, 0.0, 0.8),
            (-0.05, 0.05, -0.05, -0.05, 0.05, 0.0, 0.8),
            # 恢复站立
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2),
            # 右前
            (0.05, -0.05, -0.05, -0.05, 0.0, 0.05, 0.8),
            (0.08, -0.08, -0.1, -0.1, 0.0, 0.10, 0.8),
            (0.1, -0.1, -0.15, -0.15, 0.0, 0.12, 0.8),
            (0.08, -0.08, -0.1, -0.1, 0.0, 0.10, 0.8),
            (0.05, -0.05, -0.05, -0.05, 0.0, 0.05, 0.8),
            # 恢复站立
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2)
        ]

        for _ in range(4):
            for pose in sequence:
                rospy.loginfo("(left_shoulder, right_shoulder, left_elbow, right_elbow, left_knee, right_knee, duration) = %s", pose)
                self.walk(*pose)

        self.home(duration=1.0)


def main():
    rospy.init_node("walk_show", anonymous=True)
    show = WalkShow()
    show.run_show()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
