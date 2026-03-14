#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
import os

def publish_image(img_dir):
  rospy.init_node('image_publisher', anonymous=True)
  pub = rospy.Publisher("t_image", Image, queue_size=10)
  rate = rospy.Rate(1)  # 1hz
  bridge = CvBridge()

  img_index = 0
  img_list = os.listdir(img_dir)
  img_total_count = len(img_list)
  while not rospy.is_shutdown():
    # Create an image message and publish it
    img_path = os.path.join(img_dir, img_list[img_index])
    img = cv2.imread(img_path)
    pub.publish(bridge.cv2_to_imgmsg(img, "bgr8"))
    rospy.loginfo(f"Published image: {img_list[img_index]}")
    # update the image index
    img_index = (img_index + 1) % img_total_count
    rate.sleep()

if __name__ == '__main__':
  img_dir = "/home/andrew/Desktop/xuetangx/images/"
  publish_image(img_dir)