#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅相机话题，保存一帧图像到当前目录

使用方法：
  1. 确保 camera_demo.launch 已运行
  2. rosrun humanoid_sim save_camera_image.py
  3. 图片保存后脚本自动退出
"""

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


def save_image(msg):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    cv2.imwrite('camera_snapshot.jpg', cv_image)
    rospy.loginfo("图像已保存: camera_snapshot.jpg (%dx%d)", msg.width, msg.height)
    rospy.signal_shutdown("done")


def main():
    rospy.init_node('save_camera_image', anonymous=True)
    rospy.loginfo("等待相机图像...")
    rospy.Subscriber('/camera/image_raw', Image, save_image)
    rospy.spin()


if __name__ == '__main__':
    main()
