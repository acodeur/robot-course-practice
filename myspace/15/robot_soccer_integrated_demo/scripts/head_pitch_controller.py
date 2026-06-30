#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import Float32MultiArray, Float64


def _clamp(value, low, high):
    return max(low, min(high, value))


class HeadTrackerController:
    def __init__(self):
        rospy.init_node("head_pitch_controller")

        self.rate_hz = rospy.get_param("~rate_hz", 20.0)
        self.default_yaw = rospy.get_param("~default_yaw", 0.0)
        self.default_pitch = rospy.get_param("~default_pitch", 0.45)
        self.min_yaw = rospy.get_param("~min_yaw", -1.0)
        self.max_yaw = rospy.get_param("~max_yaw", 1.0)
        self.min_pitch = rospy.get_param("~min_pitch", -0.35)
        self.max_pitch = rospy.get_param("~max_pitch", 0.75)
        self.yaw_gain = rospy.get_param("~yaw_gain", 0.035)
        self.pitch_gain = rospy.get_param("~pitch_gain", 0.030)
        self.return_gain = rospy.get_param("~return_gain", 0.02)
        self.detection_timeout = rospy.get_param("~detection_timeout", 0.5)
        self.yaw_command_topic = rospy.get_param(
            "~yaw_command_topic", "/humanoid/head_yaw_controller/command"
        )
        self.pitch_command_topic = rospy.get_param(
            "~pitch_command_topic", "/humanoid/head_pitch_controller/command"
        )

        self.yaw = self.default_yaw
        self.pitch = self.default_pitch
        self.latest_detection = None
        self.latest_detection_time = rospy.Time(0)

        self.yaw_pub = rospy.Publisher(self.yaw_command_topic, Float64, queue_size=10)
        self.pitch_pub = rospy.Publisher(self.pitch_command_topic, Float64, queue_size=10)
        self.det_sub = rospy.Subscriber(
            "vision/detections", Float32MultiArray, self._detection_callback, queue_size=1
        )

        rospy.loginfo(
            "head_tracker: vision/detections -> %s, %s",
            self.yaw_command_topic,
            self.pitch_command_topic,
        )

    def _detection_callback(self, msg):
        if len(msg.data) < 2:
            return
        self.latest_detection = msg
        self.latest_detection_time = rospy.Time.now()

    def _fresh_detection(self):
        if self.latest_detection is None:
            return None
        if (rospy.Time.now() - self.latest_detection_time).to_sec() > self.detection_timeout:
            return None
        return self.latest_detection

    def _step_toward_default(self):
        self.yaw += self.return_gain * (self.default_yaw - self.yaw)
        self.pitch += self.return_gain * (self.default_pitch - self.pitch)

    def run(self):
        rate = rospy.Rate(self.rate_hz)

        while not rospy.is_shutdown():
            detection = self._fresh_detection()
            if detection is None:
                self._step_toward_default()
            else:
                x_error = detection.data[0]
                y_error = detection.data[1]
                self.yaw = _clamp(self.yaw - self.yaw_gain * x_error, self.min_yaw, self.max_yaw)
                self.pitch = _clamp(
                    self.pitch + self.pitch_gain * y_error,
                    self.min_pitch,
                    self.max_pitch,
                )

            self.yaw_pub.publish(Float64(data=self.yaw))
            self.pitch_pub.publish(Float64(data=self.pitch))
            rate.sleep()


if __name__ == "__main__":
    try:
        HeadTrackerController().run()
    except rospy.ROSInterruptException:
        pass
