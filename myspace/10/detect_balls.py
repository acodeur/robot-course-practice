"""作业 10.2 — 三张足球图的统一检测脚本.

每张图按其特点选不同的颜色空间 / 滤波 / 阈值, 流程统一为:
    读图 -> 滤波 -> HSV 阈值 -> 形态学 -> 轮廓 -> 圆度筛选 -> bbox/质心

对 ball_01 (球与白线粘连) 额外用 HoughCircles 兜底.
"""
from __future__ import annotations

import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
IMG_DIR = HERE / "images"
OUT_ROOT = HERE / "outputs"


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def save(out_dir: Path, name: str, img: np.ndarray) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / name), img)


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


def contour_circularity(c: np.ndarray) -> float:
    area = cv2.contourArea(c)
    perim = cv2.arcLength(c, True)
    if perim <= 0:
        return 0.0
    return 4 * np.pi * area / (perim * perim)


# ---------------------------------------------------------------------------
# ball_01 — 经典黑白球 + 绿色草地 + 白色角球线
#   颜色空间: HSV — 草地的 H 集中, 是最容易判别 "非球" 区域的特征.
#   滤波: 高斯 (5x5). 这张图的草地纹理是细密高频, 高斯能把纹理平滑而保留
#         球的轮廓. 没有明显椒盐噪声, 高斯比中值快.
#   阈值: 用课程提示的 (18,43,6)-(115,203,205) 切草地, 再反掩 -> 剩 "球+白线".
#   关键难点: 球与白线粘连, 单靠形态学切不开. 改用 HoughCircles 在反掩 mask
#         的 ROI 内直接找圆.
# ---------------------------------------------------------------------------
def detect_ball_01() -> dict:
    name = "ball_01"
    out_dir = OUT_ROOT / name
    img = cv2.imread(str(IMG_DIR / f"{name}.png"))
    save(out_dir, "step0_original.png", img)

    # 1. 滤波
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    save(out_dir, "step1_blurred.png", blurred)

    # 2. HSV + 切草地反掩
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    grass = cv2.inRange(hsv, (18, 43, 6), (115, 203, 205))
    mask = cv2.bitwise_not(grass)
    save(out_dir, "step2_mask_raw.png", mask)

    # 3. 形态学: 中等开 + 闭, 让球区域更实心 (白线仍会粘连, 没关系)
    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, ko)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kc)
    save(out_dir, "step3_cleaned.png", cleaned)

    # 4. HoughCircles 在灰度图上找圆, 用 cleaned 把搜索范围限制在 mask 内
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_masked = cv2.bitwise_and(gray, gray, mask=cleaned)
    save(out_dir, "step4_gray_masked.png", gray_masked)
    circles = cv2.HoughCircles(
        gray_masked, cv2.HOUGH_GRADIENT,
        dp=1.2, minDist=80,
        param1=120, param2=25,
        minRadius=25, maxRadius=80,
    )

    if circles is None:
        # 兜底: 用轮廓圆度筛选
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        c = max((c for c in contours if cv2.contourArea(c) > 1000),
                key=contour_circularity, default=None)
        if c is None:
            print(f"  [{name}] 检测失败")
            return {"name": name, "ok": False}
        x, y, w, h = cv2.boundingRect(c)
        m = cv2.moments(c)
        cx = int(m["m10"] / m["m00"]); cy = int(m["m01"] / m["m00"])
    else:
        # 取累加分数最高的那个圆 (HoughCircles 返回顺序按强度)
        c = np.round(circles[0, 0]).astype(int)
        cx, cy, r = int(c[0]), int(c[1]), int(c[2])
        x, y, w, h = cx - r, cy - r, 2 * r, 2 * r

    vis = draw_result(img, (x, y, w, h), (cx, cy))
    save(out_dir, "step5_detection.png", vis)
    print(f"  [{name}] bbox=({x}, {y}, {w}, {h})  centroid=({cx}, {cy})")
    return {"name": name, "ok": True, "bbox": (x, y, w, h),
            "centroid": (cx, cy)}


# ---------------------------------------------------------------------------
# ball_02 — 橙蓝球, 背景有绿色草地 + 鞋子.
#   颜色空间: HSV — 球身的橙色 H 集中在 5~20, 与背景的绿色 (60~80) 距离很远.
#   滤波: 中值 5x5. 球面有少量反光小白点 (脉冲噪声), 中值保边去白点效果好.
#   阈值: 直接命中橙色, H=0~25, S>=80, V>=80 排除阴影.
# ---------------------------------------------------------------------------
def detect_ball_02() -> dict:
    name = "ball_02"
    out_dir = OUT_ROOT / name
    img = cv2.imread(str(IMG_DIR / f"{name}.png"))
    save(out_dir, "step0_original.png", img)

    blurred = cv2.medianBlur(img, 5)
    save(out_dir, "step1_blurred.png", blurred)

    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # mask = cv2.inRange(hsv, (0, 80, 80), (25, 255, 255))
    mask = cv2.inRange(hsv, (0, 0, 0), (25, 255, 255))
    save(out_dir, "step2_mask_raw.png", mask)

    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, ko)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kc)
    save(out_dir, "step3_cleaned.png", cleaned)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 500]
    if not contours:
        print(f"  [{name}] 检测失败")
        return {"name": name, "ok": False}
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    m = cv2.moments(c)
    cx = int(m["m10"] / m["m00"]); cy = int(m["m01"] / m["m00"])

    vis = draw_result(img, (x, y, w, h), (cx, cy))
    save(out_dir, "step5_detection.png", vis)
    print(f"  [{name}] bbox=({x}, {y}, {w}, {h})  centroid=({cx}, {cy})")
    return {"name": name, "ok": True, "bbox": (x, y, w, h),
            "centroid": (cx, cy)}


# ---------------------------------------------------------------------------
# ball_03 — 白色球带黑色花纹 + 浓密草地.
#   颜色空间: HSV — 白色球的特征是 "S 低 + V 高", 草地是 "S 中高 + H 绿".
#   滤波: 双边 9. 草地纹理高频, 但球边缘要保留 — 双边滤波在平滑草纹的同时
#         保留边缘, 比高斯更适合; 单图代价可接受.
#   阈值: 切 "白色高亮" (S<60, V>180); 再用最大轮廓 + 圆度筛远景小亮块.
# ---------------------------------------------------------------------------
def detect_ball_03() -> dict:
    name = "ball_03"
    out_dir = OUT_ROOT / name
    img = cv2.imread(str(IMG_DIR / f"{name}.png"))
    save(out_dir, "step0_original.png", img)

    blurred = cv2.bilateralFilter(img, 9, 75, 75)
    save(out_dir, "step1_blurred.png", blurred)

    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # mask = cv2.inRange(hsv, (0, 0, 170), (180, 60, 255))  # 白色高亮
    mask = cv2.inRange(hsv, (62,0,0), (122,63,202))  # 白色高亮
    save(out_dir, "step2_mask_raw.png", mask)

    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kc)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, ko)
    save(out_dir, "step3_cleaned.png", cleaned)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 1000]
    if not contours:
        print(f"  [{name}] 检测失败")
        return {"name": name, "ok": False}
    # 综合面积 + 圆度
    def score(c):
        return contour_circularity(c) * 0.6 + (cv2.contourArea(c) / 1e5) * 0.4
    c = max(contours, key=score)
    x, y, w, h = cv2.boundingRect(c)
    m = cv2.moments(c)
    cx = int(m["m10"] / m["m00"]); cy = int(m["m01"] / m["m00"])

    vis = draw_result(img, (x, y, w, h), (cx, cy))
    save(out_dir, "step5_detection.png", vis)
    print(f"  [{name}] bbox=({x}, {y}, {w}, {h})  centroid=({cx}, {cy})")
    return {"name": name, "ok": True, "bbox": (x, y, w, h),
            "centroid": (cx, cy)}


def main() -> None:
    print("[detect_balls] 三张图中足球目标检测")
    results = [detect_ball_01(), detect_ball_02(), detect_ball_03()]
    print("\n[summary]")
    for r in results:
        if r.get("ok"):
            print(f"  {r['name']}: bbox={r['bbox']}  centroid={r['centroid']}")
        else:
            print(f"  {r['name']}: 检测失败")


if __name__ == "__main__":
    main()
