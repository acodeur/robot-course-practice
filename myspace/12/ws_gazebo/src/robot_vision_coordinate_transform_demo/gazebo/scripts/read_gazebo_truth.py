#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取 Gazebo 中目标物的真值位置，并保存为一个简单 YAML 文件。

默认读取模型：
  target_ball

默认输出：
  gazebo_truth/target_ball_truth.yaml
"""

from pathlib import Path

import rospy
import rospkg
from gazebo_msgs.msg import ModelStates


def package_dir():
    return Path(rospkg.RosPack().get_path("robot_vision_coordinate_transform_demo"))


def write_truth(path, model_name, pose):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"model_name: {model_name}\n")
        f.write("frame: gazebo_world\n")
        f.write("position:\n")
        f.write(f"  x: {pose.position.x:.6f}\n")
        f.write(f"  y: {pose.position.y:.6f}\n")
        f.write(f"  z: {pose.position.z:.6f}\n")
        f.write("orientation:\n")
        f.write(f"  x: {pose.orientation.x:.6f}\n")
        f.write(f"  y: {pose.orientation.y:.6f}\n")
        f.write(f"  z: {pose.orientation.z:.6f}\n")
        f.write(f"  w: {pose.orientation.w:.6f}\n")


def main():
    rospy.init_node("read_gazebo_truth", anonymous=True)

    # model_name = rospy.get_param("~model_name", "target_ball")
    model_name = rospy.get_param("~model_name", "green_reference_box")
    default_output = package_dir() / "gazebo_truth" / f"{model_name}_truth.yaml"
    output = Path(rospy.get_param("~output", str(default_output))).expanduser()

    rospy.loginfo("等待 /gazebo/model_states ...")
    msg = rospy.wait_for_message("/gazebo/model_states", ModelStates, timeout=10.0)

    if model_name not in msg.name:
        rospy.logerr("找不到模型 %s。当前模型列表: %s", model_name, msg.name)
        raise SystemExit(1)

    index = msg.name.index(model_name)
    pose = msg.pose[index]
    write_truth(output, model_name, pose)

    rospy.loginfo(
        "Gazebo 真值已保存: %s, position=(%.3f, %.3f, %.3f)",
        output,
        pose.position.x,
        pose.position.y,
        pose.position.z,
    )


if __name__ == "__main__":
    main()
