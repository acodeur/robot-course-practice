#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import rospy
import time
import yaml

sys.path.append("/home/lemon/catkin_ws/src/aelos_smart_ros")
from leju import *

cv2_img = None
leju_variable_chest_y = None
H_real=0.12

HERE = Path(__file__).resolve().parent
IMG_DIR = HERE / "images"
OUT_ROOT = HERE / "outputs"
IMG_CHEST = "chest_camera_capture.png"
IMG_HEAD = "head_camera_capture.png"
IMG_DECT_CHEST = "chest_camera_capture_dect.png"
IMG_DECT_HEAD = "head_camera_capture_dect.png"
DEBUG = False
R_ROBOT_CAMERA = np.array(
    [
        [0.0, 0.0, 1.0],
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
    ],
    dtype=float,
)
T_ROBOT_CAMERA = np.array([0.03, 0.0, 0.32], dtype=float)


def save(out_dir: Path, name: str, img: np.ndarray) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / name), img)
    print(f"保存图像: {out_dir / name}")

def draw_result(img: np.ndarray, bbox: tuple, centroid: tuple) -> np.ndarray:
    x, y, w, h = bbox
    cx, cy = centroid
    vis = img.copy()
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 3)
    cv2.drawMarker(vis, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 25, 3)
    cv2.putText(vis, f"bbox=({x},{y},{w},{h})", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(vis, f"centroid=({cx},{cy})", (8, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return vis

def get_img(camera):
    bridge = CvBridge()
    name = IMG_CHEST if camera == "chest" else IMG_HEAD
    try:
        if camera == "head":
            msg = rospy.wait_for_message('/usb_cam_head/image_raw', Image)
        elif camera == "chest":
            msg = rospy.wait_for_message('/usb_cam_chest/image_raw', Image)
        else:
            raise Exception('设备指令错误')

        cv2_img = bridge.imgmsg_to_cv2(msg, "bgr8")
        # 获取一张 Aelos 相机图像
        save(OUT_ROOT, name, cv2_img)
        # cv2_img = cv2.imread(str(OUT_ROOT / name))
        return cv2_img
    except Exception as e:
        print(e)


def colour_Silhouettes(cv_image, H_MIN, S_MIN, V_MIN, H_MAX , S_MAX , V_MAX):
    """获取最大轮廓
    """

    HSV = [(H_MIN, S_MIN, V_MIN ), (H_MAX , S_MAX , V_MAX)]

    aim_frame  = cv2.inRange(cv_image , *HSV)
    aim_frame  = cv2.erode(aim_frame , None, iterations=2)
    aim_frame  = cv2.dilate(aim_frame , np.ones((3, 3), np.uint8), iterations=2)

    contours, hierachy2 = cv2.findContours(aim_frame , cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours.sort(key=lambda c: cv2.contourArea(c), reverse=True)
    dts = cv2.drawContours(cv_image, contours, 0,(0, 0, 255),cv2.FILLED)
    return contours


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main():
    camera = "chest"
    LOOP = True
    nodes.node_initial()
    try:
        while LOOP:
            cv2_img_cam = get_img(camera)
            cv2_img = cv2.cvtColor(cv2_img_cam, cv2.COLOR_BGR2HSV)
            cv2_img = cv2.GaussianBlur(cv2_img, (3, 3), 0)
            contours = colour_Silhouettes(cv2_img, 1, 87, 113, 178, 255, 183)
            if len(contours) > 0:
                x, y, w, h = cv2.boundingRect(contours[0])
                # 计算目标像素点(u,v)
                u = x + w / 2.0
                v = y + h / 2.0
                print("目标像素点(u,v)：", (u, v))
                # 获取检测图像
                vis = draw_result(cv2_img_cam, (x, y, w, h), (int(u), int(v)))
                save(OUT_ROOT, IMG_DECT_CHEST if camera == "chest" else IMG_DECT_HEAD, vis)
                # 计算目标 bbox_xyxy
                bbox_xyxy = (x, y, x + w, y + h)
                print("目标 bbox_xyxy：", bbox_xyxy)
                # 计算 camera_ray
                camera_params = load_yaml(HERE / "camera_info" / "chest_camera.yaml")
                fx = camera_params["camera_matrix"]["data"][0]
                fy = camera_params["camera_matrix"]["data"][4]
                cx = camera_params["camera_matrix"]["data"][2]
                cy = camera_params["camera_matrix"]["data"][5]
                camera_ray = np.array([(u - cx) / fx, (v - cy) / fy, 1.0])
                print("相机射线(camera_ray)：", camera_ray)
                # 深度估计
                depth_z = fy * H_real / h
                # 计算目标在相机坐标系下的位置
                p_camera = camera_ray * depth_z
                print("目标在相机坐标系下的位置p_camera：", p_camera)
                # 计算目标在机器人坐标系下的位置
                p_robot = R_ROBOT_CAMERA @ p_camera + T_ROBOT_CAMERA
                print("目标在机器人坐标系下的位置p_robot：", p_robot)
                LOOP = False
            time.sleep(0.1)

    except Exception as e:
        nodes.serror(e)
        exit(2)
    finally:
        nodes.finishsend()
if __name__ == "__main__":
    print ("Run custom project")
    main()
