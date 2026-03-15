#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 小海龟自主走三角形 - 开环轨迹控制
import rospy
from geometry_msgs.msg import Twist
import math

# 等边三角形边长
line_length = 5.0
# 小海龟线速度和角速度
linear_speed = 1.0
angular_speed = 1.0
# 轨迹循环次数
loop = 3

def open_trace_ctl():

  rospy.init_node('open_trace_ctl', anonymous=True)
  pub = rospy.Publisher("turtle1/cmd_vel", Twist, queue_size=10)
  rate = rospy.Rate(10)
  cmd_vel = Twist()
  rospy.loginfo("小海龟自主走三角形 - 开环轨迹控制")
  i = 0
  while not rospy.is_shutdown() and i < loop * 3:
    # 沿线移动
    cmd_vel.linear.x = linear_speed
    cmd_vel.angular.z = 0.0
    start = rospy.Time.now().to_sec()
    move_length = 0.0
    line_num = i % 3 + 1
    while True:
      move_length_computed = (rospy.Time.now().to_sec() - start) * linear_speed
      if move_length_computed >= line_length:
        break
      pub.publish(cmd_vel)
      move_length = move_length_computed
      rospy.loginfo(f"已前进距离: {move_length:.5f} m")
      rate.sleep()
    rospy.loginfo(f"已完成三角形第 {line_num} 条边的前进，共前进 {move_length:.5f} m")
    # 原地旋转
    cmd_vel.linear.x = 0.0
    cmd_vel.angular.z = angular_speed
    start = rospy.Time.now().to_sec()
    rotation = 0.0
    while True:
      rotation_computed = (rospy.Time.now().to_sec() - start) * angular_speed
      if rotation_computed >= math.pi * 2.0 / 3.0:
        break
      pub.publish(cmd_vel)
      rotation = rotation_computed
      rospy.loginfo(f"已旋转角度: {rotation:.3f} rad")
      rate.sleep()
    rospy.loginfo(f"已完成三角形第 {line_num} 条边的转弯，共旋转 {rotation:.3f} rad")
    i += 1


if __name__ == '__main__':
  try:
    open_trace_ctl()
  except rospy.ROSInterruptException:
    pass
