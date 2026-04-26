#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
步态行走演示脚本（键盘 + rqt_reconfigure）
========================================
键盘控制方向，rqt_reconfigure 实时调参。

用法：
  1. 启动仿真：roslaunch humanoid_sim humanoid_walk.launch
  2. 运行步态节点：rosrun humanoid_sim walk_demo.py
  3. 在此终端用键盘控制方向：
     W=前进  S=后退  A=左移  D=右移  Q=左转  E=右转  Space=停止
  4. （可选）打开调参界面：rosrun rqt_reconfigure rqt_reconfigure

特性：
  - 持续运行，Ctrl+C 退出
  - 键盘 WASDQE + Space 切换行走方向
  - rqt_reconfigure 实时调节步态参数
  - 退出时自动回到零位
"""

import select
import sys
import termios
import time
import tty
import threading
import csv

import rospy
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Empty

from ikwalk_engine import (
    IKWalkParameters,
    IKWalkOutputs,
    IKWalkEngine,
    angles_to_ros_command,
)

# dynamic_reconfigure 编译后生成的绑定
from humanoid_sim.cfg import WalkParamsConfig
from dynamic_reconfigure.server import Server


# ---------- 行走模式 ----------
MODE_STOP       = 0
MODE_FORWARD    = 1
MODE_BACKWARD   = 2
MODE_LEFT       = 3
MODE_RIGHT      = 4
MODE_TURN_LEFT  = 5
MODE_TURN_RIGHT = 6

MODE_NAMES = {
    MODE_STOP:       "停止",
    MODE_FORWARD:    "前进",
    MODE_BACKWARD:   "后退",
    MODE_LEFT:       "左移",
    MODE_RIGHT:      "右移",
    MODE_TURN_LEFT:  "左转",
    MODE_TURN_RIGHT: "右转",
}

# 按键 → 模式映射
KEY_MAP = {
    'w': MODE_FORWARD,
    's': MODE_BACKWARD,
    'a': MODE_LEFT,
    'd': MODE_RIGHT,
    'q': MODE_TURN_LEFT,
    'e': MODE_TURN_RIGHT,
    ' ': MODE_STOP,
}


def get_key(settings, timeout=0.05):
    """非阻塞读取单个按键（Linux termios）"""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class WalkDemoNode:
    """步态行走 ROS 节点"""

    def __init__(self):
        rospy.init_node('walk_demo', anonymous=False)

        # Publisher
        self.pub = rospy.Publisher(
            '/humanoid/position_controller/command',
            Float64MultiArray,
            queue_size=10
        )

        # 步态引擎
        self.engine = IKWalkEngine()
        self.params = IKWalkParameters()
        self.params.enabledGain = 1.0

        # rqt_reconfigure 调参值（线程安全）
        self.lock = threading.Lock()
        self.current_mode = MODE_STOP

        # 从 rqt_reconfigure 读取的调参值
        self.step_gain   = 0.02
        self.turn_gain   = 0.2
        self.lateral_gain = 0.02

        # dynamic_reconfigure 服务端（只管参数，不管方向）
        self.srv = Server(WalkParamsConfig, self._reconfigure_callback)

        # 保存终端设置（退出时恢复）
        self.term_settings = termios.tcgetattr(sys.stdin)

        # Gazebo 重置服务（R 键触发）
        # 优先 reset_world：重置姿态但不回拨仿真时间，避免 RViz/TF 报错。
        rospy.loginfo("等待 Gazebo 重置服务...")
        rospy.wait_for_service('/gazebo/reset_world', timeout=30)
        self.reset_world = rospy.ServiceProxy('/gazebo/reset_world', Empty)
        self.reset_sim = rospy.ServiceProxy('/gazebo/reset_simulation', Empty)

        # 等待控制器连接
        rospy.loginfo("等待控制器连接...")
        while self.pub.get_num_connections() == 0 and not rospy.is_shutdown():
            rospy.sleep(0.1)
        rospy.loginfo("控制器已连接")

        # 初始化零位
        self._send_zero_pose(times=50)

        # 数据记录（用于生成 CSV）
        self.frame_records = []
        rospy.on_shutdown(self._cleanup)

    # ---------- dynamic_reconfigure 回调（只管调参） ----------
    def _reconfigure_callback(self, config, level):
        """rqt_reconfigure 参数变更回调——只更新步态参数，不管方向"""
        with self.lock:
            self.params.freq        = config.freq
            self.params.riseGain    = config.rise_gain
            self.params.swingGain   = config.swing_gain
            self.step_gain          = config.step_gain
            self.turn_gain          = config.turn_gain
            self.lateral_gain       = config.lateral_gain
            # 重心参数
            self.params.trunkPitch   = config.trunk_pitch
            self.params.trunkZOffset = config.trunk_z_offset
        rospy.loginfo(
            "参数更新: freq=%.1f step=%.3f rise=%.3f swing=%.3f turn=%.2f lateral=%.3f "
            "trunkPitch=%.3f trunkZ=%.3f",
            config.freq, config.step_gain, config.rise_gain,
            config.swing_gain, config.turn_gain, config.lateral_gain,
            config.trunk_pitch, config.trunk_z_offset
        )
        return config

    # ---------- 键盘监听线程 ----------
    def _keyboard_thread(self):
        """后台线程：监听 WASDQE + Space + R 按键"""
        while not rospy.is_shutdown():
            key = get_key(self.term_settings, timeout=0.05)
            if key in KEY_MAP:
                new_mode = KEY_MAP[key]
                with self.lock:
                    old_mode = self.current_mode
                    self.current_mode = new_mode
                if old_mode != new_mode:
                    rospy.loginfo("[模式] %s", MODE_NAMES[new_mode])
            elif key == 'r':
                self._reset_simulation()
            elif key == '\x03':  # Ctrl+C
                rospy.signal_shutdown("用户中断")
                break

    # ---------- 仿真重置 ----------
    def _safe_sleep(self, duration):
        """兼容仿真时间回跳的 sleep。"""
        try:
            rospy.sleep(duration)
        except rospy.exceptions.ROSTimeMovedBackwardsException:
            rospy.logwarn("[时间] 检测到仿真时间回跳，改用墙钟等待 %.2fs", duration)
            time.sleep(duration)

    def _reset_simulation(self):
        """R 键：重置 Gazebo 场景，机器人回到初始姿态。"""
        with self.lock:
            self.current_mode = MODE_STOP
        rospy.loginfo("[复位] 正在重置仿真...")
        try:
            self.reset_world()
        except rospy.ServiceException as e:
            rospy.logwarn("[复位] reset_world 失败，回退到 reset_simulation: %s", e)
            try:
                self.reset_sim()
            except rospy.ServiceException as e2:
                rospy.logwarn("[复位] 重置失败: %s", e2)
                return
        self._safe_sleep(2.0)
        self.engine.phase = 0.0  # 重置步态引擎相位
        self._send_zero_pose(times=50)
        rospy.loginfo("[复位] 完成，机器人已回到初始姿态")

    # ---------- 零位发送 ----------
    def _send_zero_pose(self, times=50):
        """发送零位姿态"""
        zero_outputs = self.engine.get_zero_pose()
        zero_cmd = angles_to_ros_command(zero_outputs)
        for _ in range(times):
            if rospy.is_shutdown():
                return
            msg = Float64MultiArray()
            msg.data = zero_cmd
            self.pub.publish(msg)
            self._safe_sleep(0.02)

    def _record_frame(self, t, phase, outputs):
        """记录当前帧数据"""
        record = {
            'time': t,
            'phase': phase,
            'left_hip_yaw': outputs.left_hip_yaw,
            'left_hip_roll': outputs.left_hip_roll,
            'left_hip_pitch': outputs.left_hip_pitch,
            'left_knee': outputs.left_knee,
            'left_ankle_pitch': outputs.left_ankle_pitch,
            'left_ankle_roll': outputs.left_ankle_roll,
            'right_hip_yaw': outputs.right_hip_yaw,
            'right_hip_roll': outputs.right_hip_roll,
            'right_hip_pitch': outputs.right_hip_pitch,
            'right_knee': outputs.right_knee,
            'right_ankle_pitch': outputs.right_ankle_pitch,
            'right_ankle_roll': outputs.right_ankle_roll,
        }
        self.frame_records.append(record)

    def _generate_csv(self):
        """生成 CSV 文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_filename = f"walk_data_{timestamp}.csv"
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.frame_records[0].keys())
            writer.writeheader()
            writer.writerows(self.frame_records)
        rospy.loginfo("[录制] 数据已保存至: %s", csv_filename)

    def _cleanup(self):
        """节点关闭后的清理工作"""
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.term_settings)
        rospy.loginfo("正在回到零位...")
        self._send_zero_pose(times=100)
        rospy.loginfo("步态节点已退出")
        # 生成 CSV 文件
        self._generate_csv()


    # ---------- 主循环 ----------
    def run(self):
        """持续运行步态循环"""
        dt = 0.02  # 50 Hz
        rate = rospy.Rate(1.0 / dt)

        # 启动键盘监听线程
        kb_thread = threading.Thread(target=self._keyboard_thread, daemon=True)
        kb_thread.start()

        # 打印操作说明
        print("\n" + "=" * 50)
        print("  步态节点已就绪")
        print("  键盘: W=前进 S=后退 A=左移 D=右移")
        print("        Q=左转 E=右转 Space=停止")
        print("        R=重置仿真（机器人摔倒后按此键）")
        print("  调参: rosrun rqt_reconfigure rqt_reconfigure")
        print("  退出: Ctrl+C")
        print("=" * 50 + "\n")

        # 累计模拟时间
        t = 0.0
        while not rospy.is_shutdown():
            with self.lock:
                mode = self.current_mode
                # 复制参数基础值
                params = IKWalkParameters()
                params.distHipToKnee    = self.params.distHipToKnee
                params.distKneeToAnkle  = self.params.distKneeToAnkle
                params.distAnkleToGround= self.params.distAnkleToGround
                params.distFeetLateral  = self.params.distFeetLateral
                params.freq             = self.params.freq
                params.riseGain         = self.params.riseGain
                params.swingGain        = self.params.swingGain
                params.enabledGain      = 1.0
                # trunk 参数
                params.trunkXOffset     = self.params.trunkXOffset
                params.trunkZOffset     = self.params.trunkZOffset
                params.trunkPitch       = self.params.trunkPitch
                params.trunkRoll        = self.params.trunkRoll
                # 样条参数
                params.swingPhase       = self.params.swingPhase
                params.swingPause       = self.params.swingPause
                params.swingVel         = self.params.swingVel
                params.stepUpVel        = self.params.stepUpVel
                params.stepDownVel      = self.params.stepDownVel
                params.riseUpVel        = self.params.riseUpVel
                params.riseDownVel      = self.params.riseDownVel

                step_gain   = self.step_gain
                turn_gain   = self.turn_gain
                lateral_gain = self.lateral_gain

            # 根据键盘模式设置方向参数
            if mode == MODE_STOP:
                params.enabledGain = 0.0
            elif mode == MODE_FORWARD:
                params.stepGain    = +step_gain
                params.turnGain    = 0.0
                params.lateralGain = 0.0
            elif mode == MODE_BACKWARD:
                params.stepGain    = -step_gain
                params.turnGain    = 0.0
                params.lateralGain = 0.0
            elif mode == MODE_LEFT:
                params.stepGain    = 0.0
                params.turnGain    = 0.0
                params.lateralGain = +lateral_gain
            elif mode == MODE_RIGHT:
                params.stepGain    = 0.0
                params.turnGain    = 0.0
                params.lateralGain = -lateral_gain
            elif mode == MODE_TURN_LEFT:
                params.stepGain    = 0.0
                params.turnGain    = +turn_gain
                params.lateralGain = 0.0
            elif mode == MODE_TURN_RIGHT:
                params.stepGain    = 0.0
                params.turnGain    = -turn_gain
                params.lateralGain = 0.0

            if mode == MODE_STOP:
                self._send_zero_pose(times=1)
                try:
                    rate.sleep()
                except rospy.exceptions.ROSTimeMovedBackwardsException:
                    rospy.logwarn_throttle(1.0, "[时间] 仿真时间回跳，跳过本周期等待")
                continue

            # 计算步态
            result = self.engine.compute(dt, params)
            # 更新累计模拟时间
            t += dt

            if result is not None:
                cmd = angles_to_ros_command(result)
                msg = Float64MultiArray()
                msg.data = cmd
                self.pub.publish(msg)
                # 记录数据
                self._record_frame(t, self.engine.phase, result)
            else:
                rospy.logwarn_throttle(1.0, "IK 求解失败，跳过此帧")

            try:
                rate.sleep()
            except rospy.exceptions.ROSTimeMovedBackwardsException:
                rospy.logwarn_throttle(1.0, "[时间] 仿真时间回跳，跳过本周期等待")

def main():
    try:
        node = WalkDemoNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
