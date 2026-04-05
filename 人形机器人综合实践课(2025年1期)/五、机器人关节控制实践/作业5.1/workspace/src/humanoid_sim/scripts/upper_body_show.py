#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upper-body show motion for the humanoid robot.

Features:
- One built-in upper-body dance motion
- Legs are always kept still

Usage:
  roslaunch humanoid_sim humanoid_control.launch
    rosrun humanoid_sim upper_body_show.py
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


class UpperBodyShow:
    def __init__(self):

        self.index = {name: i for i, name in enumerate(JOINT_ORDER)}
        self.command = [0.0] * len(JOINT_ORDER)

        self.pub = rospy.Publisher(
            "/humanoid/position_controller/command",
            Float64MultiArray,
            queue_size=10,
        )

        rospy.sleep(1.0)
        rospy.loginfo("UpperBodyShow ready")

    def _keep_legs_still(self):
        self.command[self.index["left_hip_pitch"]] = 0.0
        self.command[self.index["right_hip_pitch"]] = 0.0
        self.command[self.index["left_knee"]] = 0.0
        self.command[self.index["right_knee"]] = 0.0

    def _publish(self):
        self._keep_legs_still()
        self.pub.publish(Float64MultiArray(data=self.command))

    def move_upper(self, l_shoulder, r_shoulder, l_elbow, r_elbow, duration=0.8, rate_hz=30.0):
        duration = max(0.05, duration)
        rate_hz = max(10.0, rate_hz)

        target = list(self.command)
        target[self.index["left_shoulder_pitch"]] = l_shoulder
        target[self.index["right_shoulder_pitch"]] = r_shoulder
        target[self.index["left_elbow"]] = l_elbow
        target[self.index["right_elbow"]] = r_elbow

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
        self.move_upper(0.0, 0.0, 0.0, 0.0, duration=duration)

    def run_show(self):
        rospy.loginfo("Run upper-body dance show")
        self.home(duration=1.0)

        sequence = [
            # (left_shoulder, right_shoulder, left_elbow, right_elbow, duration)
            (1.0, -1.0, -0.8, -0.8, 0.6),
            (0.3, -0.3, -1.3, -1.3, 0.45),
            (1.2, 0.2, -1.0, -0.2, 0.5),
            (0.2, -1.2, -0.2, -1.0, 0.5),
            (0.9, -0.9, -1.1, -1.1, 0.5),
            (0.0, 0.0, 0.0, 0.0, 0.4),
        ]

        for _ in range(4):
            for pose in sequence:
                self.move_upper(*pose)

        self.home(duration=1.0)


def main():
    rospy.init_node("upper_body_show", anonymous=True)
    show = UpperBodyShow()
    show.run_show()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
