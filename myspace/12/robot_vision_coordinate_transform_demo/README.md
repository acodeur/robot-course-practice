# robot_vision_coordinate_transform_demo

本节课目标：从 Gazebo 相机图像出发，经过 YOLO 检测和坐标计算，得到目标在机器人坐标系下的大致位置。

## 一、本节课要完成什么

本节课的操作路线是：

```text
启动 Gazebo 场景
    ↓
保存相机图像
    ↓
读取 Gazebo 真值
    ↓
运行 YOLO 检测
    ↓
得到 bbox_xyxy
    ↓
计算目标像素点 (u,v)
    ↓
计算相机射线 camera_ray
    ↓
估计相机坐标 P_camera
    ↓
转换到机器人坐标 P_robot
```

---

## 二、目录说明

资料包目录如下：

```text
robot_vision_coordinate_transform_demo/
├── gazebo/          # Gazebo world、URDF 和 ROS 辅助脚本
├── launch/          # ROS 启动文件
├── yolo/            # YOLO 权重、图片和检测输出
├── config/          # 相机内参、外参、bbox 样例和参数
├── scripts/         # 坐标计算脚本
├── gazebo_truth/    # Gazebo 真值输出目录
├── package.xml
├── CMakeLists.txt
└── requirements.txt
```

其中：

- `yolo/models/yolo11n.pt`：YOLO 预训练模型权重。
- `config/sample_bbox.yaml`：YOLO 检测失败时使用的示例检测框。
- `config/camera_intrinsics.yaml`：相机内参。
- `config/extrinsics_robot_camera.yaml`：相机到机器人坐标系的外参。

---

## 三、放到 ROS 工作空间

建议把资料包放到 ROS 工作空间的 `src` 目录下。

如果资料包在当前目录，可以执行：

```bash
mkdir -p ~/ws_gazebo/src
cp -r robot_vision_coordinate_transform_demo ~/ws_gazebo/src/
cd ~/ws_gazebo
```

给 Gazebo 辅助脚本增加可执行权限：

```bash
chmod +x src/robot_vision_coordinate_transform_demo/gazebo/scripts/*.py
```

编译工作空间：

```bash
catkin_make
```

刷新 ROS 工作空间环境：

```bash
source devel/setup.bash
```

## 四、启动 Gazebo 场景

在终端中执行：

```bash
cd ~/ws_gazebo
source devel/setup.bash
roslaunch robot_vision_coordinate_transform_demo camera_demo.launch
```

Gazebo 会启动一个静态场景。

本节课中机器人默认不动，Gazebo 只用于提供相机图像和目标真值。

---

## 五、保存一帧相机图像

新开一个终端，执行：

```bash
cd ~/ws_gazebo
source devel/setup.bash
rosrun robot_vision_coordinate_transform_demo save_gazebo_image.py
```

默认保存到：

```text
robot_vision_coordinate_transform_demo/yolo/images/gazebo_camera.png
```

如果看到图像保存成功，说明 Gazebo 相机图像已经接出来了。

---

## 六、读取 Gazebo 目标真值

继续在终端中执行：

```bash
rosrun robot_vision_coordinate_transform_demo read_gazebo_truth.py
```

默认保存到：

```text
robot_vision_coordinate_transform_demo/gazebo_truth/target_ball_truth.yaml
```

这个文件记录的是 Gazebo 中目标球的真实位置，用来和后面的计算结果做对比。

---

## 七、进入 YOLO 环境

如果第十一讲已经创建过 YOLO 环境，直接激活：

```bash
conda activate robot_yolo
```

进入资料包目录：

```bash
cd ~/ws_gazebo/src/robot_vision_coordinate_transform_demo
```

安装本资料包需要的 Python 依赖：

```bash
pip install -r requirements.txt
```

---

## 八、运行 YOLO 检测

对 Gazebo 保存的图片运行 YOLO 检测：

```bash
python yolo/scripts/detect_image.py --image yolo/images/gazebo_camera.png
```

如果当前系统有图形界面，程序可能会弹出检测结果窗口。

如果不想弹窗，可以执行：

```bash
python yolo/scripts/detect_image.py --image yolo/images/gazebo_camera.png --no-show
```

检测结果会保存到：

```text
yolo/outputs/detections.yaml
```

如果 YOLO 对 Gazebo 图像识别不稳定，可以继续往下做。后续脚本会在没有有效检测结果时，使用：

```text
config/sample_bbox.yaml
```

作为示例检测框。

---

## 九、运行坐标计算

执行完整离线坐标计算流程：

```bash
python scripts/run_offline_pipeline.py
```

程序会依次计算：

```text
target_pixel (u,v)
camera_ray
P_camera
P_robot
Gazebo truth comparison
```

主要输出文件在：

```text
yolo/outputs/
```

常见输出包括：

```text
target_pixel.yaml
camera_ray.yaml
coordinate_transform_result.yaml
```

---

## 十、查看结果

运行完成后，终端会打印类似信息：

```text
depth_method: known_size
Z: 1.866 m
P_camera: Xc=0.002, Yc=0.106, Zc=1.866
P_robot:  Xr=1.956, Yr=-0.002, Zr=0.999
Gazebo truth: [2.0, 0.0, 1.0]
error norm: 0.044 m
```

---

## 十一、常见问题

### 1. `rospack find` 找不到功能包

通常是没有编译或没有刷新环境。

请重新执行：

```bash
cd ~/ws_gazebo
catkin_make
source devel/setup.bash
```

### 2. Gazebo 启动很慢或黑屏

虚拟机中 Gazebo 加载可能较慢，可以等待一会儿。

如果一直异常，可以尝试重新打开终端后再次启动。

### 3. YOLO 没有检测出目标

这是允许的。

Gazebo 图像和真实照片有差异，YOLO 可能识别不稳定。

继续执行：

```bash
python scripts/run_offline_pipeline.py
```

程序会使用 `config/sample_bbox.yaml` 继续完成坐标计算。

### 4. 缺少 Python 依赖

请确认已经进入 YOLO 环境，并安装依赖：

```bash
conda activate robot_yolo
pip install -r requirements.txt
```
