#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第六讲 2R 手臂运动学工具
所有连杆参数与 humanoid_kinematics.urdf 完全一致。

用法:
  arm_kinematics.py fk <q1> <q2>              正运动学
  arm_kinematics.py ik <s> <d>                逆运动学 (2R 平面坐标)
  arm_kinematics.py ik --torso <y> <z>        逆运动学 (torso 坐标系)
  arm_kinematics.py reach <s> <d>             可达性检查
  arm_kinematics.py multi <s> <d>             多解对比 (肘弯曲 vs 肘反向)

示例:
  arm_kinematics.py fk 0.8 -0.9
  arm_kinematics.py ik 0.10 0.30
  arm_kinematics.py ik --torso 0.15 0.10
  arm_kinematics.py reach 0.10 0.50
  arm_kinematics.py multi 0.10 0.30
"""
import math
import sys

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


def to_torso(s, d):
    """(s, d) → torso 坐标系 (x, y, z)"""
    return SHOULDER_IN_TORSO[0], s, SHOULDER_IN_TORSO[2] - d


def rostopic_cmd(q1, q2):
    return (f'rostopic pub /humanoid/position_controller/command '
            f'std_msgs/Float64MultiArray '
            f'"data: [{q1:.4f}, 0.0, {q2:.4f}, 0.0, 0.0, 0.0, 0.0, 0.0]" -1')


# ==================== fk 子命令 ====================
def cmd_fk(args):
    q1 = float(args[0]) if len(args) > 0 else 0.8
    q2 = float(args[1]) if len(args) > 1 else -0.9
    q1_limited, q2_limited = False, False
    # 限位判断
    if q1 < Q1_LIMITS[0]:
        q1 = Q1_LIMITS[0]
        q1_limited = True
    elif q1 > Q1_LIMITS[1]:
        q1 = Q1_LIMITS[1]
        q1_limited = True

    if q2 < Q2_LIMITS[0]:
        q2 = Q2_LIMITS[0]
        q2_limited = True
    elif q2 > Q2_LIMITS[1]:
        q2 = Q2_LIMITS[1]
        q2_limited = True

    s, d = fk_2r(q1, q2)
    x, y, z = to_torso(s, d)

    print("=" * 55)
    print(f"输入: q1 = {q1:.4f} rad ({math.degrees(q1):.1f} deg) {'限位' if q1_limited else ''}")
    print(f"      q2 = {q2:.4f} rad ({math.degrees(q2):.1f} deg) {'限位' if q2_limited else ''}")
    print()
    print(f"手端 (torso 系): x={x:.4f}, y={y:.4f}, z={z:.4f}")
    print(f"  ↑ 应与 tf_echo /torso /left_hand 的 Translation 一致")
    print()
    print(f"2R 平面坐标: s={s:.4f} (侧向), d={d:.4f} (下垂)")
    print("=" * 55)
    print()
    print(">>> 对应的关节命令:")
    print(rostopic_cmd(q1, q2))


# ==================== ik 子命令 ====================
def cmd_ik(args):
    if len(args) >= 3 and args[0] == "--torso":
        y_t, z_t = float(args[1]), float(args[2])
        s_target = y_t
        d_target = SHOULDER_IN_TORSO[2] - z_t
        print(f"torso 目标: y={y_t:.3f}, z={z_t:.3f}")
        print(f"转换 → 2R 平面: s={s_target:.3f}, d={d_target:.3f}")
        print()
    elif len(args) >= 2:
        s_target, d_target = float(args[0]), float(args[1])
    else:
        s_target, d_target = 0.10, 0.30

    r2 = s_target ** 2 + d_target ** 2
    c2 = (r2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)

    if abs(c2) > 1.0:
        r = math.sqrt(r2)
        print(f"目标点不可达: |c2| = {abs(c2):.4f} > 1")
        print(f"目标距离 = {r:.4f} m, 可达范围 = [{RMIN:.2f}, {RMAX:.2f}] m")
        sys.exit(1)

    q2 = -math.acos(c2)
    q1 = math.atan2(s_target, d_target) - math.atan2(
        L2 * math.sin(q2), L1 + L2 * math.cos(q2)
    )

    s_fk, d_fk = fk_2r(q1, q2)
    err = math.sqrt((s_fk - s_target) ** 2 + (d_fk - d_target) ** 2)
    _, y_fk, z_fk = to_torso(s_fk, d_fk)

    q1_ok = Q1_LIMITS[0] <= q1 <= Q1_LIMITS[1]
    q2_ok = Q2_LIMITS[0] <= q2 <= Q2_LIMITS[1]

    print("=" * 55)
    print(f"目标: s = {s_target:.4f} m, d = {d_target:.4f} m")
    print(f"q1 = {q1:.4f} rad ({math.degrees(q1):.1f} deg)  限位{'OK' if q1_ok else 'FAIL'}")
    print(f"q2 = {q2:.4f} rad ({math.degrees(q2):.1f} deg)  限位{'OK' if q2_ok else 'FAIL'}")
    print(f"FK 验证: s={s_fk:.4f}, d={d_fk:.4f}, 误差={err:.6f} m")
    print(f"末端 torso 坐标: x=0.130, y={y_fk:.4f}, z={z_fk:.4f}")
    print()
    if q1_ok and q2_ok:
        print(">>> 可直接粘贴到终端发送给机器人:")
        print(rostopic_cmd(q1, q2))
    else:
        print(">>> 超出关节限位，无法执行")
    print("=" * 55)


# ==================== reach 子命令 ====================
def cmd_reach(args):
    s = float(args[0]) if len(args) > 0 else 0.10
    d = float(args[1]) if len(args) > 1 else 0.50

    r = math.sqrt(s ** 2 + d ** 2)
    c2 = (s ** 2 + d ** 2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)

    print(f"目标: s = {s}, d = {d}")
    print(f"目标到肩关节距离: r = {r:.4f} m")
    print(f"可达范围: [{RMIN:.2f}, {RMAX:.2f}] m")
    print(f"c2 = {c2:.4f}")
    print()
    if abs(c2) > 1.0:
        print(f"|c2| = {abs(c2):.4f} > 1 → 目标点不可达")
        if r > RMAX:
            print(f"原因: 目标距离 {r:.3f} > 最大可达距离 {RMAX:.2f}")
        elif r < RMIN:
            print(f"原因: 目标距离 {r:.3f} < 最小可达距离 {RMIN:.2f}")
    else:
        print("目标点可达")


# ==================== multi 子命令 ====================
def cmd_multi(args):
    s_target = float(args[0]) if len(args) > 0 else 0.10
    d_target = float(args[1]) if len(args) > 1 else 0.30

    r2 = s_target ** 2 + d_target ** 2
    c2 = (r2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)

    if abs(c2) > 1.0:
        print("目标点不可达")
        sys.exit(1)

    print(f"目标: s = {s_target}, d = {d_target}")
    print()

    for name, sign in [("解 A (q2 < 0, 肘弯曲)", -1),
                        ("解 B (q2 > 0, 肘反向)", +1)]:
        q2 = sign * math.acos(c2)
        q1 = math.atan2(s_target, d_target) - math.atan2(
            L2 * math.sin(q2), L1 + L2 * math.cos(q2)
        )
        s_fk, d_fk = fk_2r(q1, q2)

        q1_ok = Q1_LIMITS[0] <= q1 <= Q1_LIMITS[1]
        q2_ok = Q2_LIMITS[0] <= q2 <= Q2_LIMITS[1]

        print(f"{name}:")
        print(f"  q1 = {q1:+.4f} rad ({math.degrees(q1):+.1f} deg)  "
              f"限位{'OK' if q1_ok else 'FAIL'}")
        print(f"  q2 = {q2:+.4f} rad ({math.degrees(q2):+.1f} deg)  "
              f"限位{'OK' if q2_ok else 'FAIL'}")
        print(f"  FK check: s={s_fk:.4f}, d={d_fk:.4f}")
        if q1_ok and q2_ok:
            print(f"  >>> 可用:")
            print(f"  {rostopic_cmd(q1, q2)}")
        else:
            print(f"  >>> 超出 URDF 关节限位，不可用")
        print()


# ==================== 主入口 ====================
COMMANDS = {
    "fk": cmd_fk,
    "ik": cmd_ik,
    "reach": cmd_reach,
    "multi": cmd_multi,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    COMMANDS[sys.argv[1]](sys.argv[2:])
