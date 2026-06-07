cmake_minimum_required(VERSION 3.0.2)
project(robot_vision_coordinate_transform_demo)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  gazebo_msgs
  cv_bridge
)

catkin_package()

catkin_install_python(PROGRAMS
  gazebo/scripts/save_gazebo_image.py
  gazebo/scripts/read_gazebo_truth.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
