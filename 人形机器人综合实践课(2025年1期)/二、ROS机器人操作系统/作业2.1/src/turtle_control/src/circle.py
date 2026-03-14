#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist

def move_circle():
    rospy.init_node('circle_mover', anonymous=True)
    pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rate = rospy.Rate(10)  # 10 Hz

    move_cmd = Twist()
    move_cmd.linear.x = 1.0  # Move forward at 1.0 m/s
    move_cmd.angular.z = 1.0  # Rotate at 1.0 rad/s

    while not rospy.is_shutdown():
        pub.publish(move_cmd)
        rate.sleep()

if __name__ == '__main__':
    try:
        move_circle()
    except rospy.ROSInterruptException:
        pass