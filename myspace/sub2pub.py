#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# subscriber to publisher

import rospy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math

# 三角形属性
side_length = 5.0
vertexes = [(side_length, 0.0), (side_length / 2.0, side_length * math.sin(math.pi / 3.0)), (0.0, 0.0)]
# 控制参数
vertex_idx = 0
distance_threshold = 0.1
angle_threshold = 0.1
# 最大/中间线速度和角速度
max_linear = side_length / 3.0
max_angular = math.pi * 2.0 / 3.0 / 3.0
mid_linear = 0.5
mid_angular = 0.5
# 增益
k_linear = 1.0
k_angular = 1.0
# 其他
pub = None
cmd_vel = Twist()
distance_rate = None
angle_rate = None
start_pose = None
start_pose_received = False
last_distance = 2 * side_length
angle_spin_flag = False

def normalize_angle(angle):
    """将角度规范化到 [-pi, pi] 区间"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle

def callback(data):
  global start_pose, start_pose_received, pub, vertexes, vertex_idx, last_distance, angle_spin_flag
  rospy.loginfo(f"小海龟当前位姿: x={data.x:.5f}, y={data.y:.5f}, theta={data.theta:.5f}")
  if not start_pose_received:
    start_pose = data
    # 更新三角形顶点坐标为相对于起始位姿的坐标
    for i in range(len(vertexes)):
      vertexes[i]= (vertexes[i][0] + start_pose.x, vertexes[i][1] + start_pose.y)
      rospy.loginfo(f"三角形第 {i+1} 个顶点坐标: x={vertexes[i][0]:.5f}, y={vertexes[i][1]:.5f}")
    start_pose_received = True
  else:
    target_x, target_y = vertexes[vertex_idx]
    dx = target_x - data.x
    dy = target_y - data.y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    rospy.loginfo(f"当前目标点: x={target_x:.5f}, y={target_y:.5f}")
    rospy.loginfo(f"到目标点的距离: {distance:.5f}")
    # distance小于阈值或者大于上一distance（跨过顶点）进行自旋
    if distance < distance_threshold or distance > last_distance or angle_spin_flag:
      rospy.loginfo(f">>>>>>>>>>>>>>> 已到达目标点 [{vertex_idx + 1}]  <<<<<<<<<<<<<<<")
      if distance > last_distance:
        rospy.logwarn(f"目标点 [{vertex_idx + 1}] 实际被跨过，后退一步")
        cmd_vel.linear.x = -1 * cmd_vel.linear.x
        cmd_vel.angular.z = 0.0
        pub.publish(cmd_vel)
        last_distance = 2 * side_length
        angle_spin_flag = True
        return 
      # 原地旋转
      vertex_idx_next = (vertex_idx + 1) % len(vertexes)
      angle = math.atan2(vertexes[vertex_idx_next][1] - data.y, vertexes[vertex_idx_next][0] - data.x)
      angle_diff = normalize_angle(angle - data.theta)
      rospy.loginfo(f"需要旋转的角度: {angle_diff:.5f} rad")
      if angle_diff > angle_threshold:
        # 先快后慢
        angular_z = 0.0
        if angle_diff < mid_angular:
          angular_z = k_angular * 0.5 * angle_diff
        else:
          angular_z = min(max_angular, k_angular * angle_diff)
        cmd_vel.linear.x = 0.0
        cmd_vel.angular.z = angular_z
        rospy.loginfo(f">>> 角速度：{angular_z:.5f} rad/s")
        pub.publish(cmd_vel)
        angle_rate.sleep()
      else:
        # 下一条边
        rospy.loginfo(f">>>>>>>>>>>>>>> 开启下一目标点: [{vertex_idx_next + 1}]")
        vertex_idx = vertex_idx_next
        last_distance = 2 * side_length
        angle_spin_flag = False
    else:
      # 沿线移动，先快后慢
      linear_x = 0.0
      if distance < mid_linear:
        # 增益缩小（增加稳定性）
        linear_x = k_linear * 0.05 * distance
      else:
        linear_x = min(max_linear, k_linear * distance)
      cmd_vel.linear.x = linear_x
      cmd_vel.angular.z = 0.0
      rospy.loginfo(f">>> 线速度：{linear_x:.5f} /s")
      pub.publish(cmd_vel)
      last_distance = distance
      distance_rate.sleep()


def main():
  global pub,distance_rate,angle_rate
  rospy.init_node("sub2pub")
  pub = rospy.Publisher("turtle1/cmd_vel", Twist, queue_size=10)
  rospy.Subscriber("turtle1/pose", Pose, callback, queue_size=1)
  distance_rate = rospy.Rate(10)  # 10Hz
  angle_rate = rospy.Rate(10)  # 10Hz
  rospy.spin()

if __name__ == "__main__":
  main()