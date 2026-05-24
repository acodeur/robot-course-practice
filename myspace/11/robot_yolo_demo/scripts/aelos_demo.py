"""Aelos 机器人 Python 编程作业 11.2.4

功能描述
--------
一个简单的「读取传感器 + 触发动作序列」自动化程序:

  1. 通过 SDK 连接到 Aelos 机器人;
  2. 读取当前电池电压 (传感器读取);
  3. 根据电压触发不同的动作序列 (自定义自动化流程):
     - 电压 < 6.5 V        → 电量低, 仅做一次挥手作为"我没电了"提示;
     - 6.5 V ≤ 电压 < 7.2 V → 电量中等, 执行 "立正 → 挥手 → 鞠躬" 的简短欢迎序列;
     - 电压 ≥ 7.2 V        → 电量充足, 执行 "立正 → 挥手 → 前进 → 转身 → 鞠躬" 的完整序列;
  4. 每个动作之间留出固定时间, 等待动作播放完毕, 避免上一个动作未结束就触发下一个导致姿态失衡;
  5. Ctrl+C 时统一回到 "立正" 姿态再断开, 避免机器人定格在不稳定姿态摔倒.

运行环境
--------
此脚本应在 Aelos 机器人**本机**的 Linux 系统上执行:
    1) 在 PC 上 SSH 连接到机器人:  ssh pi@<robot_ip>
    2) scp 把本脚本上传到机器人:  scp aelos_demo.py pi@<robot_ip>:~/
    3) 在机器人上运行:           python3 ~/aelos_demo.py

SDK 接口说明
------------
下方使用的 `aelos_robot` 模块为占位名, 不同型号的 Aelos 内置 SDK 实际包名可能是
`aelos` / `aelos_sdk` / `robot_api` / `LejuLib` 等; 函数命名约定有差异.
真实环境下请根据机器人内置 SDK 的官方文档把下面这几个函数替换为对应名称:

  | 本脚本使用                                | 常见替代名                                                |
  |------------------------------------------|----------------------------------------------------------|
  | Robot()                                  | Robot() / AelosClient() / RobotControl()                 |
  | robot.connect()                          | robot.connect() / robot.open() / 构造函数自动连接          |
  | robot.get_battery_voltage()              | robot.battery() / robot.read_sensor("battery")           |
  | robot.run_action(name)                   | robot.play_action(name) / robot.do(name) / robot.act(id) |
  | robot.list_actions()                     | robot.actions() / robot.get_action_list()                |
  | robot.disconnect()                       | robot.close() / robot.release()                          |

动作名 (stand / wave_hand / walk_forward / turn_left / bow) 也以机器人动作库中
预录入的动作名为准, 第一次跑前建议先用 robot.list_actions() 把所有可用动作打印一遍.
"""

from __future__ import annotations

import io
import sys
import time
import signal
from typing import Optional

# Windows 控制台默认 cp936, 中文打印会乱码; 在 Linux/Aelos 机器人本机不影响
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# === SDK 假定接口 ===========================================================
# 真实环境下, 请把下面这行替换为机器人内置 SDK 的真实导入,
# 例如:  from aelos import Robot, ActionNotFound
try:
    from aelos_robot import Robot, ActionNotFound  # type: ignore
except ImportError:
    # 在没有机器人 SDK 的开发机上, 用一个最小桩, 让代码语法层面可读、可调试
    class ActionNotFound(Exception):
        pass

    class Robot:                       # noqa: D401 (开发桩, 仅打日志, 不做实际动作)
        def connect(self):
            print("[stub] connect()")

        def disconnect(self):
            print("[stub] disconnect()")

        def get_battery_voltage(self) -> float:
            return 7.4                  # 假装满电

        def list_actions(self):
            return ["stand", "wave_hand", "walk_forward", "turn_left", "bow"]

        def run_action(self, name: str):
            print(f"[stub] run_action({name!r})")

# === 业务常量 ===============================================================
BATTERY_LOW = 6.5         # V
BATTERY_MID = 7.2         # V
ACTION_GAP_S = 2.0        # 每个动作之间的等待时间, 给舵机执行留出余量


# === 工具函数 ===============================================================
def safe_run(robot: Robot, action: str, valid: Optional[set] = None) -> bool:
    """安全执行一个动作: 名字不存在时打印警告, 不抛异常导致整段崩溃."""
    if valid is not None and action not in valid:
        print(f"  [skip] '{action}' 不在动作库中")
        return False
    try:
        print(f"  -> {action}")
        robot.run_action(action)
        time.sleep(ACTION_GAP_S)
        return True
    except ActionNotFound:
        print(f"  [warn] 动作 '{action}' 未找到, 跳过")
        return False


def reset_pose(robot: Robot) -> None:
    """优雅复位: 回到立正, 避免机器人定格在不稳姿态."""
    try:
        robot.run_action("stand")
        time.sleep(1.0)
    except Exception as e:                              # noqa: BLE001
        print(f"  [warn] 复位失败: {e}")


# === 主流程 =================================================================
def main() -> None:
    robot = Robot()
    robot.connect()

    # Ctrl+C 时一定要把机器人摆回立正姿态再退出
    def _on_sigint(*_):
        print("\n[exit] 接收到 Ctrl+C, 复位并退出")
        reset_pose(robot)
        robot.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_sigint)

    # 1. 列出动作库, 把可用动作放到集合里, 后续防止拼错
    available = set(robot.list_actions())
    print(f"[init] 可用动作 ({len(available)}): {sorted(available)}")

    # 2. 读取传感器: 电池电压
    voltage = robot.get_battery_voltage()
    print(f"[sensor] 电池电压 = {voltage:.2f} V")

    # 3. 自动化逻辑: 电量分档触发不同序列
    if voltage < BATTERY_LOW:
        print(f"[plan] 电量低 (< {BATTERY_LOW} V), 仅播放低电量提示动作")
        sequence = ["wave_hand"]
    elif voltage < BATTERY_MID:
        print(f"[plan] 电量中 ({BATTERY_LOW} - {BATTERY_MID} V), 短欢迎序列")
        sequence = ["stand", "wave_hand", "bow"]
    else:
        print(f"[plan] 电量足 (>= {BATTERY_MID} V), 完整欢迎序列")
        sequence = ["stand", "wave_hand", "walk_forward", "turn_left", "stand", "bow"]

    print("[run] 开始执行动作序列")
    for act in sequence:
        safe_run(robot, act, valid=available)

    # 4. 收尾: 复位 + 断开
    reset_pose(robot)
    robot.disconnect()
    print("[done] 程序正常结束")


if __name__ == "__main__":
    main()
