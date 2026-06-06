#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅 Gazebo 相机图像话题，保存一帧图片后退出。

默认输出：
  ~/ws_gazebo/src/robot_vision_coordinate_transform_demo/yolo/images/gazebo_camera.png

也可以通过 ROS 私有参数修改：
  rosrun robot_vision_coordinate_transform_demo save_gazebo_image.py _output:=/tmp/gazebo_camera.png
"""

from pathlib import Path

import cv2
import rospy
import rospkg
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


def default_output_path():
    package_dir = Path(rospkg.RosPack().get_path("robot_vision_coordinate_transform_demo"))
    return package_dir / "yolo" / "images" / "gazebo_camera.png"


def save_image(msg):
    output = Path(rospy.get_param("~output", str(default_output_path()))).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
    cv2.imwrite(str(output), cv_image)

    rospy.loginfo("图像已保存: %s (%dx%d)", output, msg.width, msg.height)
    rospy.signal_shutdown("saved one frame")


def main():
    rospy.init_node("save_gazebo_image", anonymous=True)
    topic = rospy.get_param("~topic", "/camera/image_raw")
    rospy.loginfo("等待相机图像: %s", topic)
    rospy.Subscriber(topic, Image, save_image, queue_size=1)
    rospy.spin()


if __name__ == "__main__":
    main()
