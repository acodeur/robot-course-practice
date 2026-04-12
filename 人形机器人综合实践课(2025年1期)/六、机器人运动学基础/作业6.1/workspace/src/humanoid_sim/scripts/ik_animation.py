#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2R 平面手臂 IK 可视化动画
用法:
  python3 ik_animation.py [s_target] [d_target]
  s_target — 侧向目标 (默认 0.10)
  d_target — 下垂目标 (默认 0.30)
"""
import math
import sys

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ========== URDF 参数 ==========
L1 = 0.20
L2 = 0.18

# ========== 目标点 ==========
s_target = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
d_target = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30

# ========== IK 求解 ==========
r2 = s_target ** 2 + d_target ** 2
c2 = (r2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)

if abs(c2) > 1.0:
    print(f"目标点不可达: s={s_target}, d={d_target}, |c2|={abs(c2):.4f}")
    sys.exit(1)

c2 = max(-1.0, min(1.0, c2))
q2_final = -math.acos(c2)
q1_final = math.atan2(s_target, d_target) - math.atan2(
    L2 * math.sin(q2_final), L1 + L2 * math.cos(q2_final)
)

print(f"目标: s={s_target}, d={d_target}")
print(f"IK 解: q1={q1_final:.4f} rad, q2={q2_final:.4f} rad")

# ========== 动画设置 ==========
N_FRAMES = 60

fig, ax = plt.subplots(figsize=(7, 7))


def fk(q1, q2):
    """返回 (肩, 肘, 末端) 在 (s, -d) 绘图坐标系中的坐标"""
    elbow_s = L1 * math.sin(q1)
    elbow_neg_d = -L1 * math.cos(q1)
    end_s = elbow_s + L2 * math.sin(q1 + q2)
    end_neg_d = elbow_neg_d - L2 * math.cos(q1 + q2)
    return (0, 0), (elbow_s, elbow_neg_d), (end_s, end_neg_d)


arm_line, = ax.plot([], [], 'o-', lw=4, markersize=10,
                    color='#2E86C1', zorder=3)
target_dot, = ax.plot([], [], 'X', markersize=14,
                      color='#C0392B', zorder=4)
ee_dot, = ax.plot([], [], 'o', markersize=8,
                  color='#27AE60', zorder=4)
angle_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                     va='top', fontsize=10, family='monospace')

rmax = L1 + L2
theta_arr = [i * math.pi / 90 for i in range(-90, 91)]
ax.plot([rmax * math.sin(t) for t in theta_arr],
        [-rmax * math.cos(t) for t in theta_arr],
        '--', color='gray', alpha=0.3, label=f'max reach = {rmax:.2f} m')
rmin = abs(L1 - L2)
if rmin > 0.001:
    ax.plot([rmin * math.sin(t) for t in theta_arr],
            [-rmin * math.cos(t) for t in theta_arr],
            ':', color='gray', alpha=0.2, label=f'min reach = {rmin:.2f} m')

ax.set_xlim(-0.5, 0.5)
ax.set_ylim(-0.5, 0.15)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.axhline(0, color='gray', lw=0.5)
ax.axvline(0, color='gray', lw=0.5)
ax.set_xlabel('s  (Y world, forward swing)')
ax.set_ylabel('-d  (-Z world, upward)')
ax.set_title(f'2R Arm: URDF L1={L1}, L2={L2}  |  target s={s_target}, d={d_target}')
ax.legend(loc='upper right', fontsize=8)

target_dot.set_data([s_target], [-d_target])


def animate(frame):
    t = frame / N_FRAMES
    t = 3 * t ** 2 - 2 * t ** 3
    q1 = q1_final * t
    q2 = q2_final * t
    shoulder, elbow, end_eff = fk(q1, q2)
    xs = [shoulder[0], elbow[0], end_eff[0]]
    ys = [shoulder[1], elbow[1], end_eff[1]]
    arm_line.set_data(xs, ys)
    ee_dot.set_data([end_eff[0]], [end_eff[1]])
    angle_text.set_text(
        f'q1 = {q1:+.3f} rad ({math.degrees(q1):+.1f} deg)\n'
        f'q2 = {q2:+.3f} rad ({math.degrees(q2):+.1f} deg)'
    )
    return arm_line, ee_dot, angle_text


anim = FuncAnimation(fig, animate, frames=N_FRAMES + 1,
                     interval=33, blit=True, repeat=True)
plt.tight_layout()
plt.show()
