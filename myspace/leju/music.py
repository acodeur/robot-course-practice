#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ********************
# Author : ccx
# Last Modification : 
# Comment : 
#   定义基本音乐接口
# ********************


import rospy
from aelos_smart_ros.srv import CMDcontrol

def music_play(music_name, wait_time = 20):
    rospy.wait_for_service('action_receive')
    val = rospy.ServiceProxy('action_receive', CMDcontrol)
    name = "play_{}".format(music_name)
    resp1 = val(name,wait_time)


def music_stop(wait_time = 20):
    rospy.wait_for_service('action_receive')
    val = rospy.ServiceProxy('action_receive', CMDcontrol)
    name = "music_stop"
    resp1 = val(name, wait_time)