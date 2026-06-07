#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ********************
# Author : ccx
# Last Modification : 
# Comment : 
#   获取消息接口
# ********************


import rospy
from aelos_smart_ros.srv import information

def main(s):
    rospy.wait_for_service('send_websocket_msg')
    val = rospy.ServiceProxy('send_websocket_msg', information)
    resp1 = val(s)


if __name__ == '__main__':
    main()