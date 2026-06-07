#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ********************
# Author : ccx
# Last Modification : 
# Comment : 
#   定义基本动作接口
# ********************


import rospy
from aelos_smart_ros.srv import CMDcontrol

def action(act_name, wait_time = 20):
    rospy.wait_for_service('action_receive')
    val = rospy.ServiceProxy('action_receive', CMDcontrol)
    resp1 = val(act_name, wait_time)

