"""
生成 5 自由度机械臂的 STL 模型文件。

结构设计:
  base_link  - 底座（圆柱体）
  link_1     - 肩部连杆（长方体）       Joint 1: 绕 Z 轴旋转
  link_2     - 大臂连杆（长方体）       Joint 2: 绕 Y 轴俯仰
  link_3     - 小臂连杆（圆柱体）       Joint 3: 绕 Y 轴俯仰
  link_4     - 腕部连杆（圆柱体）       Joint 4: 绕 Y 轴俯仰
  link_5     - 末端执行器（长方体）     Joint 5: 绕 Z 轴旋转
"""

import os
import math
import numpy as np
from stl import mesh


def create_cylinder(radius, height, n_segments=32):
    """创建以原点为中心的圆柱体 mesh"""
    vertices = []
    faces = []

    half_h = height / 2.0

    # 顶面和底面的中心点
    bottom_center = len(vertices)
    vertices.append([0, 0, -half_h])
    top_center = bottom_center + 1
    vertices.append([0, 0, half_h])

    # 侧面顶点
    for i in range(n_segments):
        angle = 2 * math.pi * i / n_segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append([x, y, -half_h])  # 底面点
        vertices.append([x, y, half_h])   # 顶面点

    # 底面三角形
    for i in range(n_segments):
        i0 = 2 + i * 2          # 当前底面点
        i1 = 2 + ((i + 1) % n_segments) * 2  # 下一个底面点
        faces.append([bottom_center, i1, i0])

    # 顶面三角形
    for i in range(n_segments):
        i0 = 2 + i * 2 + 1      # 当前顶面点
        i1 = 2 + ((i + 1) % n_segments) * 2 + 1  # 下一个顶面点
        faces.append([top_center, i0, i1])

    # 侧面三角形
    for i in range(n_segments):
        b0 = 2 + i * 2
        t0 = b0 + 1
        b1 = 2 + ((i + 1) % n_segments) * 2
        t1 = b1 + 1
        faces.append([b0, b1, t0])
        faces.append([t0, b1, t1])

    return np.array(vertices), np.array(faces)


def create_box(sx, sy, sz):
    """创建以原点为中心的长方体 mesh"""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    vertices = np.array([
        [-hx, -hy, -hz],  # 0
        [ hx, -hy, -hz],  # 1
        [ hx,  hy, -hz],  # 2
        [-hx,  hy, -hz],  # 3
        [-hx, -hy,  hz],  # 4
        [ hx, -hy,  hz],  # 5
        [ hx,  hy,  hz],  # 6
        [-hx,  hy,  hz],  # 7
    ])
    faces = np.array([
        [0, 2, 1], [0, 3, 2],  # 底面
        [4, 5, 6], [4, 6, 7],  # 顶面
        [0, 1, 5], [0, 5, 4],  # 前面
        [2, 3, 7], [2, 7, 6],  # 后面
        [1, 2, 6], [1, 6, 5],  # 右面
        [0, 4, 7], [0, 7, 3],  # 左面
    ])
    return vertices, faces


def build_mesh(vertices, faces):
    """从顶点和面数据创建 stl mesh 对象"""
    m = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = vertices[f[j]]
    return m


def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshes")
    os.makedirs(output_dir, exist_ok=True)

    parts = {}

    # ── base_link: 底座圆柱体 ──
    # 半径 0.12m, 高 0.08m
    v, f = create_cylinder(radius=0.12, height=0.08)
    parts["base_link"] = build_mesh(v, f)

    # ── link_1: 肩部转台 ──
    # 圆柱体, 半径 0.06m, 高 0.06m
    v, f = create_cylinder(radius=0.06, height=0.06)
    parts["link_1"] = build_mesh(v, f)

    # ── link_2: 大臂 ──
    # 长方体, 0.08 x 0.06 x 0.30m
    v, f = create_box(0.08, 0.06, 0.30)
    parts["link_2"] = build_mesh(v, f)

    # ── link_3: 小臂 ──
    # 圆柱体, 半径 0.035m, 高 0.25m
    v, f = create_cylinder(radius=0.035, height=0.25)
    parts["link_3"] = build_mesh(v, f)

    # ── link_4: 腕部 ──
    # 圆柱体, 半径 0.03m, 高 0.12m
    v, f = create_cylinder(radius=0.03, height=0.12)
    parts["link_4"] = build_mesh(v, f)

    # ── link_5: 末端执行器（简易夹爪形） ──
    # 长方体, 0.06 x 0.08 x 0.04m
    v, f = create_box(0.06, 0.08, 0.04)
    parts["link_5"] = build_mesh(v, f)

    for name, m in parts.items():
        path = os.path.join(output_dir, f"{name}.stl")
        m.save(path)
        print(f"  [OK] {path}")

    print(f"\nDone: {len(parts)} STL files saved to {output_dir}")


if __name__ == "__main__":
    main()
