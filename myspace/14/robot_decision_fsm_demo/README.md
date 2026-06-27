## 1. 环境准备

推荐使用 conda 创建独立环境：

```bash
conda create -n robot_decision_demo python=3.11 -y
conda activate robot_decision_demo
```

安装依赖：

```bash
pip install -r requirements.txt
```

检查 pygame：

```bash
python -c "import pygame; print(pygame.version.ver)"
```

## 2. 运行 baseline FSM

在资料包根目录运行：

```bash
python scripts/run_demo.py --agent baseline_fsm
```

窗口中可以看到：

- 左侧足球场景：机器人、足球、球门、射门线、射门位、轨迹；
- 右侧决策面板：当前阶段英文提示、动作命令、置信度、距离、射门位距离、射门角度误差、是否可踢；
- 底部状态时间轴和事件日志。

默认窗口是 `1600 x 1000`，可以在 `config/demo_config.json` 的 `ui.width` 和 `ui.height` 中调整显示像素尺寸。

## 3. 键盘控制

```text
Space  暂停 / 继续
R      重置场景
N      切换到下一个预设点球位置
D      模拟目标短暂丢失
+/-    调整仿真速度
Esc    退出
```

先观察一轮完整流程，再按 `D` 看目标丢失后如何进入恢复逻辑。

## 4. 可配置参数

主要参数在：

```text
config/demo_config.json
```

常用参数：

- `move_speed_mps`：机器人移动速度；
- `turn_speed_degps`：机器人转向速度；
- `approach_distance_m`：距离足球多近后开始寻找射门位；
- `shoot_pose_distance_m`：射门位在足球后方多远；
- `shoot_pose_tolerance_m`：距离射门位多近算到位；
- `align_angle_threshold_deg`：射门角度误差多小才允许踢球；
- `kick_speed_mps`：踢球初速度，默认 `0.22`；
- `ball_friction_mps2`：足球滚动减速度，默认 `0.03`；
- `phase_pause_seconds`：每次 phase 切换后的自动停顿时间；
- `kick_angle_noise_deg`：踢球角度误差，默认 `0.0`；
- `kick_speed_noise_ratio`：踢球速度误差，默认 `0.0`。

## 5. 状态机代码

```text
agents/baseline_fsm.py
```

状态机主要保留两个入口：

```python
def reset(self, config):
    ...

def decide(self, obs):
    ...
```

 `decide(obs)` 可理解成：

```text
当前状态 + 当前观测 -> 下一个状态 + 输出动作
```

核心状态转移：

| 当前状态 | 输出动作 | 退出条件 | 下一个状态 |
|---|---|---|---|
| `SEARCH_BALL` | `ROTATE_SEARCH` | 看到可靠足球 | `APPROACH_BALL` |
| `APPROACH_BALL` | `MOVE_TO_BALL` | 距离足球足够近 | `GET_BEHIND_BALL` |
| `GET_BEHIND_BALL` | `MOVE_TO_SHOOT_POSE` | 到达球后方射门位 | `ALIGN_TO_GOAL` |
| `ALIGN_TO_GOAL` | `TURN_TO_GOAL` | 对齐且可以踢球 | `KICK` |
| `KICK` | `KICK_BALL / STOP_AND_RECOVER` | 踢球动作结束，球停止后重新搜索 | `SEARCH_BALL` |
| `LOST_RECOVER` | `STOP_AND_RECOVER` | 恢复计时结束 | `SEARCH_BALL` |
