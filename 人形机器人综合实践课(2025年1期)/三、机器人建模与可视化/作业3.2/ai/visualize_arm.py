"""
可视化 5-DOF 机械臂模型 - 生成多视角渲染图
用于模拟 RViz 中的显示效果（含坐标系、关节标注）
"""
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh as stlmesh
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESH_DIR = os.path.join(BASE_DIR, "meshes")
OUT_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(OUT_DIR, exist_ok=True)

# ── 机械臂运动学链定义 ──
# 每个 link: (stl_file, color, visual_offset_z, joint_offset_z)
CHAIN = [
    {"name": "base_link",  "stl": "base_link.stl",  "color": "#4D4D4D", "vis_oz": 0,     "jnt_oz": 0.04},
    {"name": "link_1",     "stl": "link_1.stl",     "color": "#3366CC", "vis_oz": 0,     "jnt_oz": 0.03},
    {"name": "link_2",     "stl": "link_2.stl",     "color": "#E68A00", "vis_oz": 0.15,  "jnt_oz": 0.30},
    {"name": "link_3",     "stl": "link_3.stl",     "color": "#66B2D9", "vis_oz": 0.125, "jnt_oz": 0.25},
    {"name": "link_4",     "stl": "link_4.stl",     "color": "#CC3333", "vis_oz": 0.06,  "jnt_oz": 0.12},
    {"name": "link_5",     "stl": "link_5.stl",     "color": "#33CC66", "vis_oz": 0.02,  "jnt_oz": 0},
]

JOINT_NAMES = ["base_yaw (Z)", "shoulder_pitch (Y)", "elbow_pitch (Y)", "wrist_pitch (Y)", "wrist_roll (Z)"]


def load_stl_polys(filepath, offset_z, base_z):
    """Load STL and return Poly3DCollection shifted to correct position."""
    m = stlmesh.Mesh.from_file(filepath)
    polygons = []
    for tri in m.vectors:
        shifted = tri.copy()
        shifted[:, 2] += offset_z + base_z
        polygons.append(shifted.tolist())
    return polygons


def draw_frame(ax, origin, length=0.06, linewidth=2):
    """Draw a small XYZ coordinate frame at origin."""
    o = np.array(origin)
    ax.quiver(*o, length, 0, 0, color='r', arrow_length_ratio=0.3, linewidth=linewidth)
    ax.quiver(*o, 0, length, 0, color='g', arrow_length_ratio=0.3, linewidth=linewidth)
    ax.quiver(*o, 0, 0, length, color='b', arrow_length_ratio=0.3, linewidth=linewidth)


def render_arm(joint_angles=None, elev=25, azim=-60, title="", filename="arm_view.png",
               show_frames=True, show_labels=True, fig_size=(10, 8)):
    """Render the arm at given joint angles (all zero by default)."""
    if joint_angles is None:
        joint_angles = [0.0] * 5

    fig = plt.figure(figsize=fig_size, dpi=120)
    ax = fig.add_subplot(111, projection='3d')

    # Accumulate Z position along the chain
    current_z = 0.0
    joint_positions = []

    for i, link in enumerate(CHAIN):
        stl_path = os.path.join(MESH_DIR, link["stl"])
        polys = load_stl_polys(stl_path, link["vis_oz"], current_z)
        collection = Poly3DCollection(polys, alpha=0.85)
        collection.set_facecolor(link["color"])
        collection.set_edgecolor('#222222')
        collection.set_linewidth(0.1)
        ax.add_collection3d(collection)

        if show_frames:
            frame_z = current_z
            draw_frame(ax, [0, 0, frame_z])

        if i < len(CHAIN) - 1:
            joint_positions.append(current_z + link["jnt_oz"])
            current_z += link["jnt_oz"]

    # Label joints
    if show_labels:
        for j, (jz, jname) in enumerate(zip(joint_positions, JOINT_NAMES)):
            offset_x = 0.15 if j % 2 == 0 else -0.20
            ax.text(offset_x, 0, jz, f"J{j+1}: {jname}",
                    fontsize=7, color='#333333',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFCC', alpha=0.8))
            ax.plot([0, offset_x * 0.7], [0, 0], [jz, jz],
                    'k--', linewidth=0.5, alpha=0.5)

    # Draw the kinematic chain center line
    chain_zs = [0]
    z = 0
    for link in CHAIN[:-1]:
        z += link["jnt_oz"]
        chain_zs.append(z)
    ax.plot([0]*len(chain_zs), [0]*len(chain_zs), chain_zs,
            'k-', linewidth=1.5, alpha=0.3)

    # Style
    max_z = current_z + 0.1
    ax.set_xlim([-0.3, 0.3])
    ax.set_ylim([-0.3, 0.3])
    ax.set_zlim([-0.05, max_z + 0.1])
    ax.set_xlabel('X (m)', fontsize=9)
    ax.set_ylabel('Y (m)', fontsize=9)
    ax.set_zlabel('Z (m)', fontsize=9)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
    ax.view_init(elev=elev, azim=azim)

    # Legend for coordinate frames
    if show_frames:
        ax.plot([], [], 'r-', linewidth=2, label='X axis')
        ax.plot([], [], 'g-', linewidth=2, label='Y axis')
        ax.plot([], [], 'b-', linewidth=2, label='Z axis')
        ax.legend(loc='upper left', fontsize=8, title='Coord Frame')

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] {out_path}")
    return out_path


def render_urdf_tree(filename="urdf_tree.png"):
    """Render a diagram of the URDF link-joint tree structure."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 6), dpi=120)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title("URDF Link-Joint Tree Structure", fontsize=14, fontweight='bold')

    links = ["base_link", "link_1", "link_2", "link_3", "link_4", "link_5"]
    joints = ["base_yaw\n(revolute, Z)",
              "shoulder_pitch\n(revolute, Y)",
              "elbow_pitch\n(revolute, Y)",
              "wrist_pitch\n(revolute, Y)",
              "wrist_roll\n(revolute, Z)"]
    colors_l = ['#4D4D4D', '#3366CC', '#E68A00', '#66B2D9', '#CC3333', '#33CC66']

    y_start = 9.0
    dy = 1.5
    x_link = 3.0
    x_joint = 7.0

    for i, link in enumerate(links):
        y = y_start - i * dy
        # Link box
        rect = plt.Rectangle((x_link - 1.2, y - 0.3), 2.4, 0.6,
                              facecolor=colors_l[i], alpha=0.7,
                              edgecolor='black', linewidth=1.5, zorder=3)
        ax.add_patch(rect)
        ax.text(x_link, y, link, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white', zorder=4)

        # Joint circle + arrow
        if i < len(joints):
            jy = y - dy / 2
            # Arrow from link to joint
            ax.annotate('', xy=(x_joint - 0.8, jy),
                        xytext=(x_link + 1.2, y - 0.3),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
            # Joint circle
            circle = plt.Circle((x_joint, jy), 0.45,
                                facecolor='#FFFFCC', edgecolor='#CC9900',
                                linewidth=2, zorder=3)
            ax.add_patch(circle)
            ax.text(x_joint, jy, joints[i], ha='center', va='center',
                    fontsize=7, zorder=4)
            # Arrow from joint to next link
            next_y = y_start - (i + 1) * dy
            ax.annotate('', xy=(x_link - 1.2, next_y + 0.3),
                        xytext=(x_joint - 0.8, jy),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    out_path = os.path.join(OUT_DIR, filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] {out_path}")
    return out_path


def render_dh_table(filename="dh_table.png"):
    """Render the DH parameter table as an image."""
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=120)
    ax.axis('off')
    ax.set_title("Modified DH Parameters - 5-DOF Arm", fontsize=13, fontweight='bold', pad=10)

    col_labels = ['Joint', 'Type', 'a (m)', 'd (m)', 'alpha (rad)', 'theta range (rad)']
    table_data = [
        ['J1: base_yaw',       'Revolute', '0',    '0.04', '0',      '[-3.14, 3.14]'],
        ['J2: shoulder_pitch',  'Revolute', '0',    '0.03', 'pi/2',   '[-1.57, 1.57]'],
        ['J3: elbow_pitch',     'Revolute', '0.30', '0',    '0',      '[-2.35, 2.35]'],
        ['J4: wrist_pitch',     'Revolute', '0.25', '0',    '0',      '[-2.00, 2.00]'],
        ['J5: wrist_roll',      'Revolute', '0',    '0.12', '-pi/2',  '[-3.14, 3.14]'],
    ]

    table = ax.table(cellText=table_data, colLabels=col_labels,
                     loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)

    # Style header
    for j in range(len(col_labels)):
        table[0, j].set_facecolor('#3366CC')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        color = '#F0F0F0' if i % 2 == 0 else '#FFFFFF'
        for j in range(len(col_labels)):
            table[i, j].set_facecolor(color)

    out_path = os.path.join(OUT_DIR, filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  [OK] {out_path}")
    return out_path


def main():
    print("Generating visualization images...")

    # 1) 默认姿态 - 正视图
    render_arm(title="5-DOF Arm - Default Pose (Front View)",
               filename="arm_front.png", elev=15, azim=-70)

    # 2) 默认姿态 - 侧视图
    render_arm(title="5-DOF Arm - Default Pose (Side View)",
               filename="arm_side.png", elev=10, azim=0)

    # 3) 默认姿态 - 俯视图
    render_arm(title="5-DOF Arm - Top View",
               filename="arm_top.png", elev=80, azim=-90,
               show_labels=False)

    # 4) URDF 树结构图
    render_urdf_tree()

    # 5) DH 参数表
    render_dh_table()

    print(f"\nAll images saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
