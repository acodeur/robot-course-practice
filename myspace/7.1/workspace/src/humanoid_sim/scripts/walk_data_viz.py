#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def walk_data_viz(csv_file):
    # 定义 12 个关节列名
    left_joints = ['left_hip_yaw', 'left_hip_roll', 'left_hip_pitch',
                   'left_knee', 'left_ankle_pitch', 'left_ankle_roll']
    right_joints = ['right_hip_yaw', 'right_hip_roll', 'right_hip_pitch',
                    'right_knee', 'right_ankle_pitch', 'right_ankle_roll']
    all_joints = left_joints + right_joints
    times = []
    phases = []

    # 读取csv，存储数据为字典 {关节名: 列表}
    data = {joint: [] for joint in all_joints}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row['time']))
            phases.append(float(row['phase']))
            for joint in all_joints:
                data[joint].append(float(row[joint]))

    time = np.array(times)
    phase = np.array(phases)
    for joint in all_joints:
        data[joint] = np.array(data[joint])

    # 相位背景：左单支撑相(phase < 0.5)为绿色；右单支撑相(phase >= 0.5)为红色；
    # 实验中因IKWalkParameters.supportPhaseRatio=0.0，无双支撑相
    left_support = (phase < 0.5)
    right_support = (phase >= 0.5)

    # 创建子图：2行6列
    fig, axes = plt.subplots(2, 6, figsize=(18, 8), sharex=True)
    fig.suptitle('Gait Joint', fontsize=16)
    # 绘制左腿关节
    for i, joint in enumerate(left_joints):
        ax = axes[0, i]
        ax.plot(time, data[joint], 'b-', label=joint)
        # 填充相位区域
        ax.fill_between(time, ax.get_ylim()[0], ax.get_ylim()[1],
                        where=left_support, color='lightgreen', alpha=0.3, label='Left Support')
        ax.fill_between(time, ax.get_ylim()[0], ax.get_ylim()[1],
                        where=right_support, color='lightcoral', alpha=0.3, label='Right Support')
        ax.set_title(joint.replace('_', ' ').title())
        ax.set_ylabel('Angle (rad)')
        ax.grid(True)
        if i == 0:
            ax.legend(loc='upper right', fontsize=8)
    # 绘制右腿关节
    for i, joint in enumerate(right_joints):
        ax = axes[1, i]
        ax.plot(time, data[joint], 'r-', label=joint)
        ax.fill_between(time, ax.get_ylim()[0], ax.get_ylim()[1],
                        where=left_support, color='lightgreen', alpha=0.3)
        ax.fill_between(time, ax.get_ylim()[0], ax.get_ylim()[1],
                        where=right_support, color='lightcoral', alpha=0.3)
        ax.set_title(joint.replace('_', ' ').title())
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Angle (rad)')
        ax.grid(True)
    plt.tight_layout()
    plt.show()

    # ---------- 关节协调关系分析 ----------
    print("\n===== 关节协调关系分析 =====")

    # 1. hip_pitch与knee的关系（以左腿为例）
    hip_pitch = data['left_hip_pitch']
    knee = data['left_knee']
    # 互相关求滞后
    corr = np.correlate(hip_pitch - hip_pitch.mean(), knee - knee.mean(), mode='full')
    lag = np.argmax(corr) - (len(hip_pitch) - 1)
    dt = 0.02
    print("knee峰值滞后于hip_pitch峰值约{:.1f}ms".format(lag * dt * 1000))

    # 2. hip_roll 与 hip_pitch 的周期和相位差
    hip_roll = data['left_hip_roll']
    # 寻找峰值
    peaks_pitch, _ = find_peaks(hip_pitch)
    peaks_roll, _ = find_peaks(hip_roll)
    T_pitch = np.mean(np.diff(time[peaks_pitch]))
    T_roll = np.mean(np.diff(time[peaks_roll]))
    print(f"hip_pitch 周期 ≈ {T_pitch:.3f} s")
    print(f"hip_roll 周期 ≈ {T_roll:.3f} s，是 hip_pitch 周期的 {T_roll/T_pitch:.1f} 倍")

    # 3. 左右腿同名关节的关系（以 hip_pitch 为例）
    r_hip_pitch = data['right_hip_pitch']
    l_r_corr = np.correlate(hip_pitch - hip_pitch.mean(), r_hip_pitch - r_hip_pitch.mean(), mode='full')
    phase_shift = np.argmax(l_r_corr) - (len(hip_pitch) - 1)
    phase_frac = phase_shift / len(hip_pitch)
    print(f"左腿 hip_pitch 领先右腿 hip_pitch 约 {phase_shift} 个采样点，对应 {phase_frac:.2f} 个周期（即 {phase_frac*360:.0f}°）。")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python walk_data_viz.py <csv_file>")
        sys.exit(1)
    walk_data_viz(sys.argv[1])