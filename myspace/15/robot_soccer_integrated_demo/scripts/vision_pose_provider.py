#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

import rospy
from gazebo_msgs.msg import ModelState, ModelStates
from gazebo_msgs.srv import SetModelState
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray
from std_srvs.srv import Empty, EmptyResponse


def _yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def _relative_point(robot_pose, world_x, world_y):
    yaw = _yaw_from_quaternion(robot_pose.orientation)
    dx = world_x - robot_pose.position.x
    dy = world_y - robot_pose.position.y
    rel_x = math.cos(yaw) * dx + math.sin(yaw) * dy
    rel_y = -math.sin(yaw) * dx + math.cos(yaw) * dy
    return rel_x, rel_y


class VisionPoseProvider:
    def __init__(self):
        rospy.init_node("vision_pose_provider")

        self.robot_model = rospy.get_param("~robot_model", "robot1")
        self.ball_model = rospy.get_param("~ball_model", "soccer_ball")
        self.goal_x = rospy.get_param("~goal_x", 4.5)
        self.goal_y = rospy.get_param("~goal_y", 0.0)
        self.publish_rate = rospy.get_param("~publish_rate", 20.0)
        self.joint_state_topic = rospy.get_param("~joint_state_topic", "/humanoid/joint_states")
        self.detection_timeout = rospy.get_param("~detection_timeout", 0.5)
        self.model_timeout = rospy.get_param("~model_timeout", 1.0)
        self.joint_timeout = rospy.get_param("~joint_timeout", 1.0)

        self.horizontal_fov = rospy.get_param("~horizontal_fov", 1.047)
        self.image_width = rospy.get_param("~image_width", 640.0)
        self.image_height = rospy.get_param("~image_height", 480.0)
        self.vertical_fov = 2.0 * math.atan(
            math.tan(0.5 * self.horizontal_fov) * self.image_height / self.image_width
        )
        self.camera_x = rospy.get_param("~camera_x", 0.055)
        self.camera_y = rospy.get_param("~camera_y", 0.0)
        self.camera_z = rospy.get_param("~camera_z", 0.43)
        self.ball_center_z = rospy.get_param("~ball_center_z", 0.085)
        self.max_ball_distance = rospy.get_param("~max_ball_distance", 8.0)

        self.pause_on_score = rospy.get_param("~pause_on_score", True)
        self.score_distance = rospy.get_param("~score_distance", 0.18)
        self.score_pause_delay = rospy.get_param("~score_pause_delay", 0.5)
        self.reset_ball_x = rospy.get_param("~reset_ball_x", 1.2)
        self.reset_ball_y = rospy.get_param("~reset_ball_y", 0.0)
        self.reset_ball_z = rospy.get_param("~reset_ball_z", 0.085)
        self.reset_robot_x = rospy.get_param("~reset_robot_x", 0.0)
        self.reset_robot_y = rospy.get_param("~reset_robot_y", 0.0)
        self.reset_robot_z = rospy.get_param("~reset_robot_z", 0.0)
        self.reset_robot_yaw = rospy.get_param("~reset_robot_yaw", 0.0)

        self.detection = None
        self.detection_time = rospy.Time(0)
        self.model_states = None
        self.model_states_time = rospy.Time(0)
        self.head_yaw = 0.0
        self.head_pitch = rospy.get_param("~default_head_pitch", 0.45)
        self.joint_time = rospy.Time(0)
        self.score_detected_time = rospy.Time(0)
        self.score_handled = False

        self.ball_pub = rospy.Publisher("ball_pose", PoseStamped, queue_size=10)
        self.goal_pub = rospy.Publisher("goal_pose", PoseStamped, queue_size=10)
        self.det_sub = rospy.Subscriber(
            "vision/detections", Float32MultiArray, self._detection_callback, queue_size=1
        )
        self.joint_sub = rospy.Subscriber(
            self.joint_state_topic, JointState, self._joint_callback, queue_size=1
        )
        self.model_sub = rospy.Subscriber(
            "/gazebo/model_states", ModelStates, self._states_callback, queue_size=1
        )
        self.pause_physics = rospy.ServiceProxy("/gazebo/pause_physics", Empty)
        self.unpause_physics = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)
        self.set_model_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)
        self.reset_srv = rospy.Service("reset_ball", Empty, self._reset_ball_service)
        self.reset_demo_srv = rospy.Service("reset_demo", Empty, self._reset_demo_service)

        rospy.loginfo("vision_pose_provider: vision/detections -> ball_pose, goal_pose")

    def _detection_callback(self, msg):
        if len(msg.data) < 2:
            return
        self.detection = msg
        self.detection_time = rospy.Time.now()

    def _states_callback(self, msg):
        self.model_states = msg
        self.model_states_time = rospy.Time.now()

    def _joint_callback(self, msg):
        for name, position in zip(msg.name, msg.position):
            if name == "head_yaw":
                self.head_yaw = position
            elif name == "head_pitch":
                self.head_pitch = position
        self.joint_time = rospy.Time.now()

    def _get_robot_pose(self):
        if self.model_states is None:
            return None
        try:
            index = self.model_states.name.index(self.robot_model)
        except ValueError:
            return None
        return self.model_states.pose[index]

    def _fresh(self, stamp, timeout):
        return stamp != rospy.Time(0) and (rospy.Time.now() - stamp).to_sec() <= timeout

    def _estimate_ball_relative(self):
        if self.detection is None:
            return None

        x_error = self.detection.data[0]
        y_error = self.detection.data[1]
        yaw = self.head_yaw - x_error * 0.5 * self.horizontal_fov
        pitch = self.head_pitch + y_error * 0.5 * self.vertical_fov

        dx = math.cos(pitch) * math.cos(yaw)
        dy = math.cos(pitch) * math.sin(yaw)
        dz = -math.sin(pitch)
        if dz >= -1e-4:
            return None

        t = (self.ball_center_z - self.camera_z) / dz
        if t <= 0.0 or t > self.max_ball_distance:
            return None

        ball_x = self.camera_x + t * dx
        ball_y = self.camera_y + t * dy
        if ball_x <= 0.0:
            return None
        return ball_x, ball_y

    def _publish_pose(self, pub, rel_x, rel_y, stamp, frame_id):
        msg = PoseStamped()
        msg.header.stamp = stamp
        msg.header.frame_id = frame_id
        msg.pose.position.x = rel_x
        msg.pose.position.y = rel_y
        msg.pose.position.z = 0.0
        msg.pose.orientation.w = 1.0
        pub.publish(msg)

    def _pause_for_score(self):
        if self.score_handled:
            return
        self.score_handled = True
        if not self.pause_on_score:
            rospy.loginfo("goal scored")
            return
        try:
            rospy.wait_for_service("/gazebo/pause_physics", timeout=1.0)
            self.pause_physics()
            rospy.loginfo("goal scored; Gazebo physics paused")
        except (rospy.ROSException, rospy.ServiceException) as exc:
            rospy.logwarn("goal scored, but failed to pause Gazebo physics: %s", exc)

    def _manage_score(self, robot_pose, ball_rel):
        robot_yaw = _yaw_from_quaternion(robot_pose.orientation)
        ball_world_x = robot_pose.position.x + math.cos(robot_yaw) * ball_rel[0] - math.sin(robot_yaw) * ball_rel[1]
        ball_world_y = robot_pose.position.y + math.sin(robot_yaw) * ball_rel[0] + math.cos(robot_yaw) * ball_rel[1]
        goal_distance = math.hypot(ball_world_x - self.goal_x, ball_world_y - self.goal_y)
        if goal_distance > self.score_distance:
            return

        now = rospy.Time.now()
        if self.score_detected_time == rospy.Time(0):
            self.score_detected_time = now
            rospy.loginfo("goal scored; pausing in %.2f seconds", self.score_pause_delay)
        elif (now - self.score_detected_time).to_sec() >= self.score_pause_delay:
            self._pause_for_score()

    def _reset_ball_service(self, _req):
        self._reset_ball()
        self._unpause()
        return EmptyResponse()

    def _reset_demo_service(self, _req):
        self._reset_robot()
        self._reset_ball()
        self._unpause()
        rospy.loginfo("demo reset by service")
        return EmptyResponse()

    def _quaternion_from_yaw(self, yaw):
        q = ModelState().pose.orientation
        q.z = math.sin(0.5 * yaw)
        q.w = math.cos(0.5 * yaw)
        return q

    def _reset_robot(self):
        state = ModelState()
        state.model_name = self.robot_model
        state.reference_frame = "world"
        state.pose.position.x = self.reset_robot_x
        state.pose.position.y = self.reset_robot_y
        state.pose.position.z = self.reset_robot_z
        state.pose.orientation = self._quaternion_from_yaw(self.reset_robot_yaw)
        try:
            rospy.wait_for_service("/gazebo/set_model_state", timeout=1.0)
            self.set_model_state(state)
            rospy.loginfo("robot reset by service")
        except (rospy.ROSException, rospy.ServiceException) as exc:
            rospy.logwarn("failed to reset robot: %s", exc)

    def _reset_ball(self):
        state = ModelState()
        state.model_name = self.ball_model
        state.reference_frame = "world"
        state.pose.position.x = self.reset_ball_x
        state.pose.position.y = self.reset_ball_y
        state.pose.position.z = self.reset_ball_z
        state.pose.orientation.w = 1.0
        try:
            rospy.wait_for_service("/gazebo/set_model_state", timeout=1.0)
            self.set_model_state(state)
            self.score_handled = False
            self.score_detected_time = rospy.Time(0)
            rospy.loginfo("ball reset by service")
        except (rospy.ROSException, rospy.ServiceException) as exc:
            rospy.logwarn("failed to reset ball: %s", exc)

    def _unpause(self):
        try:
            rospy.wait_for_service("/gazebo/unpause_physics", timeout=1.0)
            self.unpause_physics()
        except (rospy.ROSException, rospy.ServiceException) as exc:
            rospy.logwarn("failed to unpause Gazebo physics: %s", exc)

    def run(self):
        rate = rospy.Rate(self.publish_rate)
        frame_id = "{}/base_link".format(self.robot_model)

        while not rospy.is_shutdown():
            now = rospy.Time.now()
            robot_pose = self._get_robot_pose()
            if robot_pose is None or not self._fresh(self.model_states_time, self.model_timeout):
                rospy.logwarn_throttle(1.0, "waiting for robot pose from /gazebo/model_states")
                rate.sleep()
                continue

            goal_x, goal_y = _relative_point(robot_pose, self.goal_x, self.goal_y)
            self._publish_pose(self.goal_pub, goal_x, goal_y, now, frame_id)

            if not self._fresh(self.detection_time, self.detection_timeout):
                rospy.logwarn_throttle(1.0, "waiting for fresh vision/detections")
                rate.sleep()
                continue
            if not self._fresh(self.joint_time, self.joint_timeout):
                rospy.logwarn_throttle(1.0, "waiting for head joint states")
                rate.sleep()
                continue

            ball_rel = self._estimate_ball_relative()
            if ball_rel is None:
                rate.sleep()
                continue

            self._publish_pose(self.ball_pub, ball_rel[0], ball_rel[1], now, frame_id)
            self._manage_score(robot_pose, ball_rel)
            rospy.loginfo_throttle(
                1.0,
                "vision ball rel_x=%.2f rel_y=%.2f head_yaw=%.2f head_pitch=%.2f",
                ball_rel[0],
                ball_rel[1],
                self.head_yaw,
                self.head_pitch,
            )
            rate.sleep()


if __name__ == "__main__":
    try:
        VisionPoseProvider().run()
    except rospy.ROSInterruptException:
        pass
