cmake_minimum_required(VERSION 3.0.2)
project(robot_soccer_integrated_demo)

find_package(catkin REQUIRED COMPONENTS
  gazebo_msgs
  gazebo_ros
  geometry_msgs
  rospy
  sensor_msgs
  std_srvs
  std_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/cmd_vel_adapter.py
  scripts/goalie_node.py
  scripts/head_pitch_controller.py
  scripts/hough_circle_detector_node.py
  scripts/vision_pose_provider.py
  scripts/soccer_demo_node.py
  scripts/yolo_detector_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(PROGRAMS
  scripts/yolo_detector_conda.sh
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY config launch models urdf worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
