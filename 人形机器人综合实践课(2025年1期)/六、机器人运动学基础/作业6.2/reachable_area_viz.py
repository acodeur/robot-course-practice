#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import matplotlib.pyplot as plt


# ==================== URDF 参数 ====================
L1 = 0.20   # 肩关节 → 肘关节
L2 = 0.18   # 肘关节 → 手端 (left_hand)
SHOULDER_IN_TORSO = (0.13, 0.0, 0.35)
Q1_LIMITS = (-1.57, 1.57)
Q2_LIMITS = (-2.0, 0.0)
RMAX = L1 + L2
RMIN = abs(L1 - L2)


def fk_2r(q1, q2):
    """2R 平面 FK → (s, d)"""
    s = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    d = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    return s, d


if __name__ == '__main__':
    print("="*50)
    print("开始绘制s-d平面散点图(手臂可达区域)")
    print("="*50)

    # 生成 q1 和 q2 的等间距值
    q1_values = [Q1_LIMITS[0] + i * (Q1_LIMITS[1] - Q1_LIMITS[0]) / 99 for i in range(100)]
    q2_values = [Q2_LIMITS[0] + j * (Q2_LIMITS[1] - Q2_LIMITS[0]) / 99 for j in range(100)]

    # 计算末端坐标
    s_values, d_values = [], []
    for q1 in q1_values:
        for q2 in q2_values:
            s, d = fk_2r(q1, q2)
            s_values.append(s)
            d_values.append(d)

    # 绘制散点图
    plt.figure(figsize=(8, 8))
    plt.scatter(s_values, d_values, s=10, color='blue', alpha=0.5)
    plt.title('Reachable Area')
    plt.xlabel('s')
    plt.ylabel('d')
    plt.axis('equal')
    plt.grid()

    # 绘制最大可达距离和最小可达距离的圆弧
    theta = [i * math.pi / 180 for i in range(360)]
    s_max = [RMAX * math.cos(t) for t in theta]
    d_max = [RMAX * math.sin(t) for t in theta]
    s_min = [RMIN * math.cos(t) for t in theta]
    d_min = [RMIN * math.sin(t) for t in theta]
    
    plt.plot(s_max, d_max, color='red', label='max reachable distance')
    plt.plot(s_min, d_min, color='green', label='min reachable distance')
    plt.legend()
    plt.show()
