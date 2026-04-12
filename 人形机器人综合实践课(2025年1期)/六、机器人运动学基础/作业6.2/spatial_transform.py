#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from scipy.spatial.transform import Rotation as R

"""
•	旋转矩阵 → RPY 欧拉角: rotation_matrix_to_rpy
•	旋转矩阵 → 四元数: rotation_matrix_to_quaternion
•	RPY 欧拉角 → 旋转矩阵: rpy_to_rotation_matrix
•	四元数 → 旋转矩阵: quaternion_to_rotation_matrix
"""

def rotation_matrix_to_rpy(rotation_matrix):
  """
    将旋转矩阵转换为 RPY 欧拉角（滚转，俯仰，偏航）。角度以弧度为单位。
  """
  r = R.from_matrix(rotation_matrix)
  # 获取依次绕 X (Roll), Y (Pitch), Z (Yaw) 轴的旋转弧度
  return r.as_euler('xyz', degrees=False)

def rotation_matrix_to_quaternion(rotation_matrix):
  """
    将旋转矩阵转换为四元数(x, y, z, w)。
  """
  r = R.from_matrix(rotation_matrix)
  return r.as_quat()

def rpy_to_rotation_matrix(rpy):
  """
    将 RPY 欧拉角（滚转，俯仰，偏航）转换为旋转矩阵。角度以弧度为单位。
  """
  roll, pitch, yaw = rpy
  r = R.from_euler('xyz', [roll, pitch, yaw], degrees=False)
  return r.as_matrix()

def quaternion_to_rotation_matrix(quaternion):
  """
    将四元数(x, y, z, w)转换为旋转矩阵。
  """
  x, y, z, w = quaternion
  r = R.from_quat([x, y, z, w])
  return r.as_matrix()


if __name__ == '__main__':
  print("="*50)
  print("开始验证各种转换方法...")
  print("="*50)

  rpy_input = np.array([0.249, -0.000, 0.000])
  quat_input = np.array([0.124, 0.000, 0.000, 0.992])
  print("\n输入数据 (来自 tf_echo 输出):")
  print(f"  RPY (rad): [{rpy_input[0]:.3f}, {rpy_input[1]:.3f}, {rpy_input[2]:.3f}]")
  print(f"  四元数 (x, y, z, w): {quat_input}")

  # RPY → 旋转矩阵 → 四元数
  rot_matrix = rpy_to_rotation_matrix(rpy_input)
  quat_from_rot = rotation_matrix_to_quaternion(rot_matrix)
  print("\nRPY → 旋转矩阵 → 四元数:")
  print(f"  旋转矩阵:\n{rot_matrix}")
  print(f"  四元数 (x, y, z, w): {quat_from_rot}")

  # 四元数 → 旋转矩阵 → RPY
  rot_matrix = quaternion_to_rotation_matrix(quat_input)
  rpy_from_rot = rotation_matrix_to_rpy(rot_matrix)

  print("\n四元数 → 旋转矩阵 → RPY:")
  print(f"  旋转矩阵:\n{rot_matrix}")
  print(f"  RPY (rad): [{rpy_from_rot[0]:.3f}, {rpy_from_rot[1]:.3f}, {rpy_from_rot[2]:.3f}]")
  
