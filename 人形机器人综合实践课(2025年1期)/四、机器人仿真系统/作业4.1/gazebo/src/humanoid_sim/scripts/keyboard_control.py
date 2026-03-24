#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零重力下人形机器人关节运动演示
通过 Gazebo 服务直接设置关节角度，无需 ros_control

使用方法：
  1. 启动 Gazebo 并加载机器人
  2. 在 Gazebo GUI 中将重力设置为 0（World → Physics → gravity z → 0）
  3. python3 control_demo_zero_gravity.py
"""

import rospy
from gazebo_msgs.srv import SetModelConfiguration, GetWorldProperties


def find_model_name():
    """自动查找 Gazebo 中的机器人模型名称（兼容拼写差异）"""
    rospy.wait_for_service('/gazebo/get_world_properties', timeout=10.0)
    srv = rospy.ServiceProxy('/gazebo/get_world_properties', GetWorldProperties)
    resp = srv()
    for name in resp.model_names:
        if name == 'ground_plane':
            continue
        rospy.loginfo("检测到模型: %s", name)
        return name
    return 'humanoid'


# 所有可动关节名称
ALL_JOINTS = [
    'left_shoulder_pitch', 'right_shoulder_pitch',
    'left_elbow', 'right_elbow',
    'left_hip_pitch', 'right_hip_pitch',
    'left_knee', 'right_knee',
]

# 预定义姿态 (与 ALL_JOINTS 顺序一一对应)
POSES = {
    '站立': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    '举左手': [1.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    '举右手': [0.0, -1.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    '双臂张开': [1.5, -1.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    '双臂弯曲': [1.5, -1.5, -1.5, -1.5, 0.0, 0.0, 0.0, 0.0],
    '蹲姿': [0.0, 0.0, 0.0, 0.0, 0.8, 0.8, 1.2, 1.2],
    '举手': [1.57, -1.57, -1.8, -1.8, 0.0, 0.0, 0.0, 0.0],
}


def set_pose(joint_names, joint_positions, model_name='humanoid'):
    """调用 Gazebo 服务设置关节角度"""
    rospy.wait_for_service('/gazebo/set_model_configuration', timeout=5.0)
    srv = rospy.ServiceProxy('/gazebo/set_model_configuration',
                             SetModelConfiguration)
    resp = srv(
        model_name=model_name,
        urdf_param_name='',
        joint_names=joint_names,
        joint_positions=joint_positions,
    )
    if not resp.success:
        rospy.logwarn("设置失败: %s", resp.status_message)
    return resp.success


def main():
    rospy.init_node('humanoid_zero_gravity_demo')

    rospy.loginfo("=" * 50)
    rospy.loginfo("  人形机器人关节运动演示（零重力）")
    rospy.loginfo("=" * 50)

    # 自动检测 Gazebo 中的机器人模型名（兼容拼写差异）
    model = find_model_name()
    rospy.loginfo("使用模型: %s", model)
    rospy.sleep(1.0)

    sequence = [
        ('站立',     2.0),
        ('举左手',   1.5),
        ('举右手',   1.5),
        ('双臂张开', 2.0),
        ('双臂弯曲', 2.0),
        ('蹲姿',     2.0),
        ('举手',     2.0),
    ]

    while not rospy.is_shutdown():
        rospy.loginfo("姿态选项:")
        for i, pose_name in enumerate(POSES.keys()):
            rospy.loginfo("  %d. %s", i + 1, pose_name)
        user_input = input("请输入姿态序号或'q'退出: ")
        if user_input == 'q':
            break
        index = int(user_input) - 1
        pose_name = list(POSES.keys())[index]
        duration = sequence[index][1]
        rospy.loginfo(">>> %s", pose_name)
        set_pose(ALL_JOINTS, POSES[pose_name], model_name=model)
        rospy.sleep(duration)

    rospy.loginfo("=" * 50)
    rospy.loginfo("  演示完成！")
    rospy.loginfo("=" * 50)


if __name__ == '__main__':
    main()
