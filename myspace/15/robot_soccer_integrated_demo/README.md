# robot_soccer_integrated_demo

- 基础环境：只启动 Gazebo、KidSize 足球场、机器人、足球、球门、相机、头部控制和 `/robot1/cmd_vel` 适配器。机器人默认不决策。
- Hough demo：在基础环境上启动 Hough 圆检测、视觉定位和决策。
- YOLO demo：在基础环境上启动 YOLO 检测、视觉定位和决策。

Hough 和 YOLO 是两个独立 demo，不同时启动。

## 1. 编译

```bash
cd ~/catkin_ws_new
catkin_make
source devel/setup.bash
```

新终端都需要：

```bash
cd ~/catkin_ws_new
source devel/setup.bash
```

## 2. 基础环境

每次 demo 都先启动基础环境：

```bash
roslaunch robot_soccer_integrated_demo soccer_env.launch
```

基础环境包含：

```text
Gazebo KidSize 足球场
robot1 人形机器人
soccer_ball
球门
/robot1/camera/image_raw
/robot1/cmd_vel
/humanoid/head_yaw_controller/command
/humanoid/head_pitch_controller/command
```

## 3. Hough 圆检测 Demo

先启动基础环境，然后另开终端：

```bash
roslaunch robot_soccer_integrated_demo soccer_hough_demo.launch
```

Hough 流程：

```text
/robot1/camera/image_raw
-> HSV 颜色阈值
-> HoughCircles 圆检测
-> /robot1/vision/detections
-> /robot1/ball_pose
-> /robot1/cmd_vel
```

查看检测图：

```bash
rqt_image_view
```

选择：

```text
/robot1/hough/debug_image
```

关闭 Hough demo 后，如果要跑 YOLO，先关闭基础环境，再重新启动基础环境。

## 4. YOLO Demo

先启动基础环境，然后另开终端：

```bash
roslaunch robot_soccer_integrated_demo soccer_yolo_demo.launch
```

YOLO 流程：

```text
/robot1/camera/image_raw
-> YOLO sports ball 检测
-> /robot1/vision/detections
-> /robot1/ball_pose
-> /robot1/cmd_vel
```

YOLO debug 图像：

```text
/robot1/yolo/debug_image
```

如果 YOLO 没有识别出 `sports ball`，YOLO demo 会用橙色圆检测作为 fallback 继续发布 `/robot1/vision/detections`。debug 图里会标注 `YOLO` 或 `FALLBACK`，用于区分真正的 YOLO 检测和兜底检测。

如果 YOLO Python 不在默认路径，启动前指定：

```bash
export ROBOT_YOLO_PYTHON=/home/ycy/miniconda3/envs/robot_yolo/bin/python
```

## 5. 视觉定位和头部控制

Hough 和 YOLO 都发布统一检测话题：

```text
/robot1/vision/detections
```

消息类型：

```text
std_msgs/Float32MultiArray
```

字段：

```text
[x_error, y_error, width_norm, height_norm, confidence, class_id]
```

`vision_pose_provider.py` 使用：

```text
图像误差
头部 yaw/pitch 角度
相机 FOV 和安装位置
球中心高度
```

估计球在机器人坐标系下的位置，并发布：

```text
/robot1/ball_pose
/robot1/goal_pose
```

机器人自身位置使用 Gazebo 发布的 `/gazebo/model_states`。

头部控制：

```text
x_error -> head_yaw
y_error -> head_pitch
```

机器人会使用头部 yaw/pitch 尽量把球保持在视野中央。

## 6. 决策输入输出

决策节点：

```text
scripts/soccer_demo_node.py
```

订阅：

```text
/robot1/ball_pose
/robot1/goal_pose
```

发布：

```text
/robot1/decision_state
/robot1/cmd_vel
```

状态包括：

```text
SEARCH_BALL
CENTER_BALL
APPROACH_BALL
DRIBBLE_BALL
SHOOT
RECOVER
```

## 7. KidSize 场地

场地按 RoboCup Humanoid League KidSize 风格设置：

```text
field: 9m x 6m
goal width: 2.6m
goal height: 1.2m
ball radius: 0.075m
```

场地包含边线、球门线、中线、中圈、中心点、球门区、禁区和罚点标线。

球门中心坐标：

```text
x = 4.5
y = 0.0
```

## 8. 进球暂停和 reset

进球后 Gazebo 物理会暂停，球不会自动重置。

手动 reset：

```bash
rosservice call /robot1/reset_ball
```

该服务会把球放回开球点并恢复 Gazebo 物理。

如果要同时重置机器人和球：

```bash
rosservice call /robot1/reset_demo
```

该服务会把 `robot1` 放回初始位置、把球放回开球点，并恢复 Gazebo 物理。

## 9. 常用检查

查看相机：

```bash
rqt_image_view
```

查看视觉检测：

```bash
rostopic echo /robot1/vision/detections
```

查看视觉估计球位置：

```bash
rostopic echo /robot1/ball_pose
```

查看决策：

```bash
rostopic echo /robot1/decision_state
rostopic echo /robot1/cmd_vel
```

如果出现 `entity already exists` 或 `new node registered with same name`，先清理旧进程：

```bash
pkill -f roslaunch
pkill -f gzserver
pkill -f gzclient
```

## 10. 双机器人自动 Hough Demo

双机器人 demo 使用 Hough，不使用 YOLO：

```bash
roslaunch robot_soccer_integrated_demo two_robot_hough_demo.launch
```

角色：

```text
robot1: attacker，使用 Hough + vision_pose_provider + soccer_demo_node 自动进攻
robot2: goalie，作为对立方守门员，使用 /gazebo/model_states 跟踪球的 y 位置，在右侧球门前防守
```

检查：

```bash
rostopic echo /robot1/decision_state
rostopic echo /robot1/cmd_vel
rostopic echo /robot2/goalie_state
rostopic echo /robot2/cmd_vel
```
