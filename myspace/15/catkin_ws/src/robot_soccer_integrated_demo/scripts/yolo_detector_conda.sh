#!/usr/bin/env bash
set -e

CONDA_PYTHON="${ROBOT_YOLO_PYTHON:-/home/ycy/miniconda3/envs/robot_yolo/bin/python}"

if [ ! -x "$CONDA_PYTHON" ]; then
  echo "robot_yolo python not found: $CONDA_PYTHON" >&2
  exit 1
fi

PKG_DIR="$(rospack find robot_soccer_integrated_demo)"
NODE_SCRIPT="$PKG_DIR/scripts/yolo_detector_node.py"

export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-/tmp/ultralytics}"
mkdir -p "$YOLO_CONFIG_DIR"

CONDA_SITE="$("$CONDA_PYTHON" -c 'import site; print(site.getsitepackages()[0])')"
export PYTHONPATH="${CONDA_SITE}:/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages:${PYTHONPATH:-}"

exec "$CONDA_PYTHON" "$NODE_SCRIPT" "$@"
