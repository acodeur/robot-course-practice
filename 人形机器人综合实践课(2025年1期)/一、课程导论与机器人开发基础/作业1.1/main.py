import time
import random

# 机器人向前移动并模拟噪声
def move_forward(current_pos, speed):
    # 模拟传感器噪声
    noise = random.uniform(-0.1, 0.1)
    step_length = speed + noise
    return current_pos + step_length

# 机器人向后移动并模拟噪声
def move_backward(current_pos, speed):
    noise = random.uniform(-0.1, 0.1)
    step_length = speed + noise
    return current_pos - step_length

if __name__ == '__main__':
    robot_name = "andrew's robot"
    battery_level = 100.0   # 电池电量
    position = 0.0          # 初始位置
    speed = 1.5             # 运行速度
    is_running = True       # 运行状态

    print(f"[{robot_name}] System Start...")
    while is_running:
        # 状态检查
        if battery_level < 20:
            print("Warning: Low Battery!")
            is_running = False
            break
        # 执行动作
        position = move_forward(position, speed)
        battery_level -= 5.0
        # 打印日志
        print(f"Status: Moving | Pos: {position:5.2f}m | Battery: {battery_level}%")
        # 控制频率
        time.sleep(0.5)

    print(f"[{robot_name}] System Shutdown!")

