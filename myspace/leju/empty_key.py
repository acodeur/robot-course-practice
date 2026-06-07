#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ********************
# Author : ccx
# Last Modification : 
# Comment : 
#   定义基本动作接口
# ********************


import rospy
from aelos_smart_ros.srv import empty_key

def key():
    rospy.wait_for_service('empty_keys')
    val = rospy.ServiceProxy('empty_keys', empty_key)
    resp1 = val("KEY")
    return resp1.key


if __name__ == '__main__':
    print(key())