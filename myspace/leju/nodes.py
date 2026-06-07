#!/usr/bin/env python
#-*- coding:utf-8 -*-

import rospy
from . import empty_key
from leju import get_websocket_msg


def node_initial():
    rospy.init_node('main_node', anonymous = True)
    empty_key.key()

def finishsend():
    pass


def serror(e):
    Exceptionstr = str(e)
    get_websocket_msg.main(Exceptionstr)
    pass