import time
import random
import matplotlib.pyplot as plt
import numpy as np

# 机器人向前移动并模拟噪声
def move_forward(current_pos, speed):
    # 模拟传感器噪声
    noise = random.uniform(-0.1, 0.1)
    step_length = speed + noise
    return current_pos + step_length

# 机器人向后移动并模拟噪声
def move_backward(current_pos, speed):
    # 模拟传感器噪声
    noise = random.uniform(-0.1, 0.1)
    step_length = speed + noise
    return current_pos - step_length

# 检测障碍物距离
def detect_obs():
    return 10 + random.random() * 20

if __name__ == '__main__':
    robot_name = "andrew's robot"
    battery_level = 100.0       # 电池电量
    speed = 1.5                 # 运行速度
    position = 0.0              # 初始位置
    obstacle_pos = detect_obs() # 障碍物位置
    is_running = True           # 运行状态
    pos_trace = [position]      # 位置轨迹

    print(f"[{robot_name}] System Start...")
    print(f"[{robot_name}] Obstacle Detected. Pos: {obstacle_pos:.2f}m")
    while is_running:
        # 电量状态检查
        if battery_level < 20:
            print("Warning: Low Battery!")
            is_running = False
            break
        # 获取下一位置用于检测
        next_position = move_forward(position, speed)
        # 检测到障碍物自动停止
        if next_position >= obstacle_pos:
            print("Warning: Obstacle Too Close!")
            is_running = False
            break
        # 执行动作，move_forward
        battery_level -= 5.0
        position = next_position
        pos_trace.append(position)
        # 打印日志
        print(f"Status: Moving | Pos: {position:5.2f}m | Battery: {battery_level}%")
        # 控制频率
        time.sleep(0.5)

    print(f"[{robot_name}] System Shutdown!")

    # 绘制轨迹
    x_points = np.array(pos_trace)
    y_points = np.ones(len(pos_trace))
    plt.plot(x_points, y_points, label="trace", marker='o', color='b', linestyle=':')
    plt.plot(obstacle_pos, 1, label="obstacle", marker='*', color='r', linestyle=':')
    plt.legend()
    plt.xlabel(f"{robot_name} trace")
    plt.show()


