import rospy
from aelos_smart_ros.srv import *


def set_input(io):
    rospy.wait_for_service('io_service')
    val = rospy.ServiceProxy('io_service', topic)
    resp1 = val("input",io,0)

def set_output(io,vol):
    rospy.wait_for_service('io_service')
    val = rospy.ServiceProxy('io_service', topic)
    resp2 = val("output",io,vol)


def get_magnet():
    rospy.wait_for_service('get_magnet')
    val = rospy.ServiceProxy('get_magnet', get_mag)
    resp3 = val("get")
    return resp3.magnet


def get_gpio(io):
    rospy.wait_for_service('get_io')
    val = rospy.ServiceProxy('get_io', get_io)
    resp4 = val(io)
    if resp4.io_status == 1:  #output
        set_input(io)
        val = rospy.ServiceProxy('get_io', get_io)
        resp4 = val(io)
    return resp4.io_adc


def get_io_status(io):
    rospy.wait_for_service('get_io')
    val = rospy.ServiceProxy('get_io', get_io)
    resp5 = val(io)
    return resp5.io_status, resp5.io_adc   # 0:inupt , 1:output