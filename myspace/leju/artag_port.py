import rospy
from ar_track_alvar_msgs.msg import AlvarMarkers
import math
import tf
import math

def get_nearest_marker(camera_str):

    if camera_str == "head":
        msg = rospy.wait_for_message('/head/ar_pose_marker', AlvarMarkers)
    else:
        msg = rospy.wait_for_message('/chest/ar_pose_marker', AlvarMarkers)

    markers = []
    time_sec = msg.header.stamp.secs
    for marker in msg.markers:
        pos = marker.pose.pose.position
        quat = marker.pose.pose.orientation

        rpy = tf.transformations.euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])
        rpy_arc = [0, 0, 0]
        for i in range(len(rpy)):
            rpy_arc[i] = rpy[i] / math.pi * 180
        

        markers.append([marker.id, pos.x, pos.y, rpy_arc[2], time_sec])
        
    markers.sort(key=lambda marker: marker[1]**2 + marker[2]**2)
    
    return markers[0]


def get_specifies_marker(camera_str):

    if camera_str == "head":
        msg = rospy.wait_for_message('/head/ar_pose_marker', AlvarMarkers)
    else:
        msg = rospy.wait_for_message('/chest/ar_pose_marker', AlvarMarkers)
    
    markers = dict()
    time_sec = msg.header.stamp.secs
    for marker in msg.markers:
        pos = marker.pose.pose.position
        quat = marker.pose.pose.orientation

        rpy = tf.transformations.euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])
        rpy_arc = [0, 0, 0]
        for i in range(len(rpy)):
            rpy_arc[i] = rpy[i] / math.pi * 180
        
        markers[marker.id] = [pos.x, pos.y, rpy_arc[2], time_sec]

    return markers


def tag_id(camera="chest"):
    try:
        msg = get_nearest_marker(camera)
        return msg[0]
    except Exception as e:
        return math.nan


def tag_x(camera="chest"):
    try:
        msg = get_nearest_marker(camera)
        return msg[1]
    except Exception as e:
        return math.nan


def tag_y(camera="chest"):
    try:
        msg = get_nearest_marker(camera)
        return msg[2]
    except Exception as e:
        return math.nan


def tag_yaw(camera="chest"):
    try:
        msg = get_nearest_marker(camera)
        return msg[3]
    except Exception as e:
        return math.nan

def get_specifies_tag(id, camera="chest"):
    marker = get_specifies_marker(camera)
    if id in marker:
        return marker[id][0], marker[id][1], marker[id][2]
    else:
        return 1000, 1000, 1000


def get_x_position(camera, id, Xmin, Xmax):
    tempValue = get_specifies_tag(id, camera)

    if tempValue[0] == 1000:
        return False
    
    return Xmin <= tempValue[0] <= Xmax

def get_y_position(camera, id, Ymin, Ymax):
    tempValue = get_specifies_tag(id, camera)
    
    if tempValue[0] == 1000:
        return False
    
    return Ymin <= -tempValue[1] <= Ymax


if __name__ == "__main__":
    rospy.init_node("artag_port")
    # result  = artag_port.get_y_position("head", 8, 0.042, 0.062)     # y影响左右
    # result1 = artag_port.get_x_position("chest", 8, 0.42, 0.62)      # X影响前后
    print(get_specifies_tag(2))

