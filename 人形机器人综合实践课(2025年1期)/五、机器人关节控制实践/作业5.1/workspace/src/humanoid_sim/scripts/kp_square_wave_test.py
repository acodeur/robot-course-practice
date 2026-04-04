#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
Kp 方波激励测试脚本
========================================
功能：
  在指定关节上发送方波位置命令，便于重复测试 Kp/Kd 响应。

默认控制接口：
  话题: /humanoid/position_controller/command
  类型: std_msgs/Float64MultiArray

用法示例：
  rosrun humanoid_sim kp_square_wave_test.py
    rosrun humanoid_sim kp_square_wave_test.py -j left_shoulder_pitch -l 0.0 -H 1.2 -p 4.0
    rosrun humanoid_sim kp_square_wave_test.py -j left_shoulder_pitch -l 0.0 -H 1.2 -p 4.0 -c 6
"""

import argparse
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


class KpSquareWaveTester:
    def __init__(self, joint_name, low, high, period, cycles, publish_rate):
        self.joint_name = joint_name
        self.joint_index = JOINT_ORDER.index(joint_name)
        self.low = low
        self.high = high
        self.period = period
        self.cycles = cycles
        self.publish_rate = publish_rate
        self.half_period = period / 2.0

        self.command = [0.0] * len(JOINT_ORDER)

        rospy.init_node("kp_square_wave_test", anonymous=True)
        self.publisher = rospy.Publisher(
            "/humanoid/position_controller/command",
            Float64MultiArray,
            queue_size=10,
        )

        rospy.sleep(1.0)

    def publish_target(self, target, log=True):
        self.command[self.joint_index] = target
        self.publisher.publish(Float64MultiArray(data=self.command))
        if log:
            rospy.loginfo(
                "joint=%s target=%.3f command=%s",
                self.joint_name,
                target,
                [round(value, 3) for value in self.command],
            )

    def hold_target(self, target, duration):
        self.command[self.joint_index] = target
        end_time = rospy.Time.now() + rospy.Duration.from_sec(duration)
        rate = rospy.Rate(self.publish_rate)

        while not rospy.is_shutdown() and rospy.Time.now() < end_time:
            self.publisher.publish(Float64MultiArray(data=self.command))
            rate.sleep()

    def run(self):
        rospy.loginfo("=" * 60)
        rospy.loginfo("开始方波激励测试")
        if self.cycles == 0:
            rospy.loginfo(
                "joint=%s low=%.3f high=%.3f period=%.2fs mode=continuous",
                self.joint_name,
                self.low,
                self.high,
                self.period,
            )
            rospy.loginfo("publish_rate=%.1f Hz", self.publish_rate)
            rospy.loginfo("按 Ctrl+C 停止")
        else:
            rospy.loginfo(
                "joint=%s low=%.3f high=%.3f period=%.2fs cycles=%d publish_rate=%.1fHz",
                self.joint_name,
                self.low,
                self.high,
                self.period,
                self.cycles,
                self.publish_rate,
            )
        rospy.loginfo("=" * 60)

        self.publish_target(self.low)
        rospy.sleep(1.0)

        if self.cycles == 0:
            cycle = 0
            while not rospy.is_shutdown():
                cycle += 1
                rospy.loginfo("cycle %d: HIGH", cycle)
                self.publish_target(self.high, log=False)
                self.hold_target(self.high, self.half_period)

                rospy.loginfo("cycle %d: LOW", cycle)
                self.publish_target(self.low, log=False)
                self.hold_target(self.low, self.half_period)
        else:
            for cycle in range(1, self.cycles + 1):
                rospy.loginfo("cycle %d/%d: HIGH", cycle, self.cycles)
                self.publish_target(self.high, log=False)
                self.hold_target(self.high, self.half_period)

                rospy.loginfo("cycle %d/%d: LOW", cycle, self.cycles)
                self.publish_target(self.low, log=False)
                self.hold_target(self.low, self.half_period)

        rospy.loginfo("测试结束，复位到 low")
        self.publish_target(self.low)


def parse_args():
    parser = argparse.ArgumentParser(description="Kp 方波激励测试")
    parser.add_argument(
        "-j",
        "--joint",
        default="left_shoulder_pitch",
        choices=JOINT_ORDER,
        help="要激励的关节名",
    )
    parser.add_argument("-l", "--low", type=float, default=0.0, help="方波低电平角度(rad)")
    parser.add_argument("-H", "--high", type=float, default=1.57, help="方波高电平角度(rad)")
    parser.add_argument("-p", "--period", type=float, default=8.0, help="方波周期(s)")
    parser.add_argument(
        "-c",
        "--cycles",
        type=int,
        default=0,
        help="方波周期次数；0 表示无限循环（默认）",
    )
    parser.add_argument(
        "-r",
        "--publish-rate",
        type=float,
        default=20.0,
        help="保持高/低电平时的重复发布频率(Hz)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.period <= 0:
        raise ValueError("period 必须 > 0")
    if args.cycles < 0:
        raise ValueError("cycles 必须 >= 0")
    if args.publish_rate <= 0:
        raise ValueError("publish-rate 必须 > 0")

    tester = KpSquareWaveTester(
        joint_name=args.joint,
        low=args.low,
        high=args.high,
        period=args.period,
        cycles=args.cycles,
        publish_rate=args.publish_rate,
    )
    tester.run()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
