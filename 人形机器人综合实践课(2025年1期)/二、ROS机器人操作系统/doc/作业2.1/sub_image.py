#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2

bridge = CvBridge()

def image_callback(msg):
  rospy.loginfo("Received an image!")
  try:
    # Image message to OpenCV format
    cv_image = bridge.imgmsg_to_cv2(msg, "bgr8")
    resized_img = cv2.resize(cv_image, (500, 500))
    cv2.imshow("ROS-动手实验：订阅图片", resized_img)
    cv2.waitKey(1)
  except CvBridgeError as e:
    rospy.logerr(f"Error converting image: {e}")


def subscribe_image():
  rospy.init_node('image_subscriber', anonymous=True)
  # 订阅t_image的消息
  rospy.Subscriber("t_image", Image, image_callback)
  # 循环等待回调函数
  rospy.spin()


if __name__ == '__main__':
  subscribe_image()