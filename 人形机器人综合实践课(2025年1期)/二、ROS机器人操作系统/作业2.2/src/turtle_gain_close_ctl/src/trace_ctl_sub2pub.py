#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 小海龟自主走三角形 - 闭环轨迹控制
import rospy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math

# 等边三角形边长
line_length = 3.0
vertex_points = [(line_length, 0.0), (line_length / 2.0, line_length * math.sin(math.pi / 3.0)), (0.0, 0.0)]
# 控制参数
linear_threshold = 0.01
angular_threshold = 0.01
max_linear = 1.0
max_angular = 2.0
# 比例增益
k_linear = 2.0
k_angular = 2.0
# 轨迹循环次数
loop = 3
line_total = loop * 3
line_count = 0
line_num = 1
# 位姿相关
pose = None
pose_received = False
# 其他
pub = None
msg_twist = Twist()
rate = None

def is_same_pose(msg, pose):
  return msg.x == pose.x and msg.y == pose.y and msg.theta == pose.theta

def move_next(pose):
  global line_num, line_count
  # 获取当前目标点
  target_x, target_y = vertex_points[line_num - 1]
  # 计算线速度和角速度
  dx = target_x - pose.x
  dy = target_y - pose.y
  distance = math.sqrt(dx ** 2 + dy ** 2)
  angular_diff = math.atan2(dy, dx) - pose.theta
  if distance > linear_threshold:
    # 向前移动
    linear_speed = min(max_linear, k_linear * distance)
    msg_twist.linear.x = linear_speed * 0.5  # 减小线速度以提高稳定性
    msg_twist.angular.z = 0.0
    pub.publish(msg_twist)
    rate.sleep()
  else:
    # 旋转角度
    angular = math.atan2(vertex_points[line_num][1] - pose.y, vertex_points[line_num][0] - pose.x)
    angular_diff = angular - pose.theta
    msg_twist.linear.x = 0.0
    msg_twist.angular.z = angular_diff
    pub.publish(msg_twist)
    rate.sleep()
    line_num = line_num % 3 + 1
    line_count += 1


  if line_count >= line_total:
    rospy.loginfo("已完成所有轨迹循环，停止小海龟")
    msg_twist.linear.x = 0.0
    msg_twist.angular.z = 0.0
    pub.publish(msg_twist)
    rospy.signal_shutdown("任务完成")

def pose_callback(msg):
  global pose, pose_received
  if not pose_received:
    pose = msg
    pose_received = True
    rospy.loginfo(f"接收到小海龟初始位姿: x={pose.x:.5f}, y={pose.y:.5f}, theta={pose.theta:.3f} rad")
  else:
    if not is_same_pose(msg, pose):
      pose = msg
      rospy.loginfo(f"接收到小海龟最新位姿: x={pose.x:.5f}, y={pose.y:.5f}, theta={pose.theta:.3f} rad")
      move_next(pose)


def close_trace_ctl():
  global pub, rate, pose_callback_count
  rospy.init_node('close_trace_ctl', anonymous=True)
  pub = rospy.Publisher("turtle1/cmd_vel", Twist, queue_size=10)
  sub = rospy.Subscriber("turtle1/pose", Pose, callback=pose_callback)
  rate = rospy.Rate(500)

  rospy.loginfo("小海龟自主走三角形 - 闭环轨迹控制")
  while not pose_received and not rospy.is_shutdown():
    rospy.loginfo("等待接收小海龟位姿...")
    rospy.sleep(0.1)
  rospy.loginfo(f"小海龟初始位姿: x={pose.x:.5f}, y={pose.y:.5f}, theta={pose.theta:.3f} rad")
  # 更新三角形顶点坐标，使其以小海龟初始位置为起点
  for i in range(3):
    vertex_points[i] = (vertex_points[i][0] + pose.x, vertex_points[i][1] + pose.y)
  rospy.loginfo(f"更新后的三角形顶点坐标: {vertex_points}")
  # 触发小海龟沿三角形轨迹移动
  move_next(pose)
  rospy.spin()


if __name__ == '__main__':
  try:
    close_trace_ctl()
  except rospy.ROSInterruptException:
    pass
