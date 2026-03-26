import cv2
import os

def process():
  cwd = os.getcwd()
  img_path = os.path.join(cwd, '人形机器人综合实践课(2025年1期)/四、机器人仿真系统/作业4.1/gazebo/camera_snapshot.jpg')
  dest_path = os.path.join(cwd, '人形机器人综合实践课(2025年1期)/四、机器人仿真系统/作业4.2')
  # 读取相机图像
  img = cv2.imread(img_path)
  # 获取灰度图
  gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  cv2.imwrite(os.path.join(dest_path, 'camera_snapshot_gray.jpg'), gray_img)
  print("灰度图已保存: camera_snapshot_gray.jpg")
  # 获取边缘图
  edge_img = cv2.Canny(gray_img, 50, 150)
  cv2.imwrite(os.path.join(dest_path, 'camera_snapshot_edges.jpg'), edge_img)
  print("边缘图已保存: camera_snapshot_edges.jpg")


if __name__ == "__main__":
  process()