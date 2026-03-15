#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import math
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

class TriangleCloseTraceCtl:
    def __init__(self):
        rospy.init_node('close_trace_ctl')
        self.pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
        self.sub = rospy.Subscriber('/turtle1/pose', Pose, self.pose_callback)
        self.rate = rospy.Rate(20)  # 20Hz控制频率

        # 控制参数
        self.max_linear = 1.0
        self.max_angular = 2.0
        self.k_linear = 1.5
        self.k_angular = 4.0
        self.dist_threshold = 0.1   # 到达判定阈值

        # 计算等边三角形顶点（边长5，中心(5.5,5.5)）
        cx, cy = 5.5, 5.5
        side = 5.0
        height = math.sqrt(3) / 2 * side          # 高 ≈ 4.33
        R = side / math.sqrt(3)                    # 外接圆半径 ≈ 2.887

        # 三个顶点坐标（逆时针顺序，从顶部顶点开始）
        self.targets = [
            (cx, cy + R),                          # 顶部顶点 (5.5, 8.387)
            (cx - side/2, cy - height/3),          # 左下顶点 (3.0, 4.057)
            (cx + side/2, cy - height/3),          # 右下顶点 (8.0, 4.057)
            (cx, cy + R)                            # 回到顶部顶点闭合
        ]

        self.current_idx = 0       # 当前目标点索引
        self.pose = None           # 最新位姿
        self.pose_received = False

    def pose_callback(self, msg):
        self.pose = msg
        self.pose_received = True

    def normalize_angle(self, angle):
        """将角度规范化到 [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def run(self):
        rospy.loginfo("等待位姿数据...")
        while not self.pose_received and not rospy.is_shutdown():
            self.rate.sleep()

        rospy.loginfo("开始闭环绘制三角形，边长5")
        while not rospy.is_shutdown():
            if self.current_idx >= len(self.targets):
                rospy.loginfo("所有目标点已到达，任务完成")
                break

            target_x, target_y = self.targets[self.current_idx]
            x = self.pose.x
            y = self.pose.y
            theta = self.pose.theta

            # 计算到目标点的距离
            dx = target_x - x
            dy = target_y - y
            distance = math.hypot(dx, dy)

            # 到达判断
            if distance < self.dist_threshold:
                rospy.loginfo("到达目标点 %d: (%.2f, %.2f)", self.current_idx, target_x, target_y)
                self.current_idx += 1
                # 短暂停顿便于观察
                self.pub.publish(Twist())
                rospy.sleep(0.5)
                continue

            # 计算期望朝向
            desired_angle = math.atan2(dy, dx)
            angle_diff = self.normalize_angle(desired_angle - theta)

            # 比例控制
            linear = min(self.max_linear, self.k_linear * distance)
            angular = min(self.max_angular, self.k_angular * angle_diff)

            # 如果角度偏差过大，优先转向（可提高直线性）
            if abs(angle_diff) > 0.5:
                linear = 0.0

            twist = Twist()
            twist.linear.x = linear
            twist.angular.z = angular
            self.pub.publish(twist)

            self.rate.sleep()

        # 最终停止
        self.pub.publish(Twist())
        rospy.loginfo("闭环控制结束")

if __name__ == '__main__':
    try:
        controller = TriangleCloseTraceCtl()
        controller.run()
    except rospy.ROSInterruptException:
        pass