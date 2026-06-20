# robot_localization_system_demo

本实验用 Python 在二维地图中演示一个最小定位系统：

```text
里程计漂移 -> 地图地标观测 -> 粒子滤波纠偏 -> 输出机器人位姿 pose
```

## 1. 环境准备

推荐使用 conda 创建独立环境：

```bash
conda create -n robot_loc_demo python=3.11 numpy matplotlib -y
conda activate robot_loc_demo
```

也可以使用 pip 安装依赖：

```bash
pip install -r requirements.txt
```

检查环境：

```bash
python -c "import numpy, matplotlib; print(numpy.__version__, matplotlib.__version__)"
```

## 2. 运行运动学累积误差展示

```bash
python scripts/dead_reckoning_demo.py
```

运行时会打开动态窗口，绿色真实轨迹和红色里程计轨迹会逐步增长，右侧误差曲线会同步刷新。

输出：

```text
outputs/01_dead_reckoning_drift.png
```

观察：只靠里程计推算时，误差会随着运动一步步累积，轨迹会逐渐偏离真实轨迹。

## 3. 运行动画版粒子滤波演示

```bash
python scripts/particle_filter_live_demo.py
```

运行时会打开动态窗口，粒子、真实轨迹、里程计轨迹和估计轨迹会逐步刷新。

输出：

```text
outputs/02_particle_filter_result.png
outputs/03_error_curve.png
outputs/metrics.txt
```

`metrics.txt` 中会输出真实位姿、里程计位姿、粒子滤波位姿，以及平均误差和末端误差。

## 4. 修改参数观察效果

主要参数在：

```text
config/demo_config.json
```

可以先尝试修改：

```json
"num_particles": 80
```

然后重新运行：

```bash
python scripts/particle_filter_live_demo.py
```

观察粒子数量变少后，定位结果是否更容易抖动。

也可以调整初始化范围：

```json
"initialization": {
  "position_std": 0.45,
  "theta_std": 0.35,
  "global_fraction": 0.15
}
```

其中 `position_std` 越大，初始粒子越分散；`global_fraction` 表示保留一部分全局随机粒子。

也可以在命令行临时覆盖粒子数量：

```bash
python scripts/particle_filter_live_demo.py --particles 80
```

## 5. 常见问题

如果动态窗口无法打开，请先使用：

```bash
python scripts/dead_reckoning_demo.py --no-show
python scripts/particle_filter_live_demo.py --no-show
```

只生成图片结果。

如果运行速度较慢，可以减少粒子数量：

```bash
python scripts/particle_filter_live_demo.py --no-show --particles 200
```
