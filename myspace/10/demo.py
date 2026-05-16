"""第十讲 OpenCV 颜色目标检测教学脚本.

按步骤演示 "读图 → 通道 → 滤波 → HSV 阈值 → 形态学 → 轮廓质心",
每一步都会弹出 cv2.imshow 窗口,按任意键进入下一步.
运行方式:
    python demo.py                                   # 默认理想图
    python demo.py --image images/02_ball_floor_bg.png
    python demo.py --tuner                           # 现场 HSV 调参
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_IMAGE = HERE / "images" / "02_ball_floor_bg.png"

# 橙色球的 HSV 默认范围 (OpenCV 约定: H ∈ [0,180], S/V ∈ [0,255])
# HSV_LOWER = np.array([5, 120, 120], dtype=np.uint8)
# HSV_UPPER = np.array([20, 255, 255], dtype=np.uint8)
HSV_LOWER = np.array([5, 120, 120], dtype=np.uint8)
HSV_UPPER = np.array([20, 255, 255], dtype=np.uint8)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
MAX_DISPLAY_W = 640  # 显示窗口宽度上限，超出则缩放


def _fit(image: np.ndarray) -> np.ndarray:
    """若图像宽度超过 MAX_DISPLAY_W, 等比缩小后返回; 否则原样返回."""
    h, w = image.shape[:2]
    if w <= MAX_DISPLAY_W:
        return image
    scale = MAX_DISPLAY_W / w
    return cv2.resize(image, (MAX_DISPLAY_W, int(h * scale)), interpolation=cv2.INTER_AREA)


def _show(title: str, image: np.ndarray, out_dir: Path, filename: str) -> None:
    """弹窗展示并同步保存到 outputs/<stem>/ 供教学手册截图使用."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / filename), image)
    cv2.imshow(title, _fit(image))


def _wait_and_close() -> None:
    print("  [按任意键进入下一步]")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ---------------------------------------------------------------------------
# Step 0: 读图与显示
# ---------------------------------------------------------------------------
def step0_read_and_show(image_path: Path, out_dir: Path) -> np.ndarray:
    print("\n[Step 0] 读图与显示 —— OpenCV 默认 BGR")
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {image_path}")
    h, w, c = img.shape
    print(f"  文件: {image_path.name}")
    print(f"  尺寸: height={h}, width={w}, channels={c}")
    print(f"  dtype: {img.dtype}  (注意: 通道顺序为 BGR, 不是 RGB)")
    _show("Step0 Original (BGR)", img, out_dir, "step0_original.png")
    _wait_and_close()
    return img


# ---------------------------------------------------------------------------
# Step 1: RGB 三通道
# ---------------------------------------------------------------------------
def step1_rgb_channels(img: np.ndarray, out_dir: Path) -> None:
    print("\n[Step 1] RGB 三通道可视化")
    b, g, r = cv2.split(img)  # OpenCV 顺序是 B,G,R
    cv2.imshow("Step1 B channel", _fit(b))
    cv2.imshow("Step1 G channel", _fit(g))
    cv2.imshow("Step1 R channel", _fit(r))
    cv2.imwrite(str(out_dir / "step1_channel_B.png"), b)
    cv2.imwrite(str(out_dir / "step1_channel_G.png"), g)
    cv2.imwrite(str(out_dir / "step1_channel_R.png"), r)
    print(f"  B mean={b.mean():.1f}  G mean={g.mean():.1f}  R mean={r.mean():.1f}")
    print("  橙色球在 R 通道上最亮, 在 B 通道上最暗 —— 但颜色筛选依旧困难")
    _wait_and_close()


# ---------------------------------------------------------------------------
# Step 2: HSV 三通道
# ---------------------------------------------------------------------------
def step2_hsv_channels(img: np.ndarray, out_dir: Path) -> np.ndarray:
    print("\n[Step 2] 转 HSV 并拆通道 ")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    cv2.imshow("Step2 H (hue, 0-180)", _fit(h))
    cv2.imshow("Step2 S (saturation)", _fit(s))
    cv2.imshow("Step2 V (value)", _fit(v))
    cv2.imwrite(str(out_dir / "step2_channel_H.png"), h)
    cv2.imwrite(str(out_dir / "step2_channel_S.png"), s)
    cv2.imwrite(str(out_dir / "step2_channel_V.png"), v)
    print(f"  H range: [{h.min()}, {h.max()}]  (OpenCV 约定 0-180)")
    print(f"  S range: [{s.min()}, {s.max()}]  V range: [{v.min()}, {v.max()}]")
    print("  橙色球在 H 通道聚集成一块稳定区域, 这正是我们能用 inRange 切出它的原因")
    _wait_and_close()
    return hsv


# ---------------------------------------------------------------------------
# Step 3: 高斯滤波
# ---------------------------------------------------------------------------
def step3_blur(img: np.ndarray, out_dir: Path) -> np.ndarray:
    print("\n[Step 3] 高斯滤波 —— 削弱噪声, 让颜色面稳定")
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    pair = np.hstack([img, blurred])
    cv2.imshow("Step3 Before | After GaussianBlur(5x5)", _fit(pair))
    cv2.imwrite(str(out_dir / "step3_blur_pair.png"), pair)
    diff = cv2.absdiff(img, blurred).mean()
    print(f"  滤波前后平均像素差: {diff:.2f}")
    print("  滤波后 HSV 阈值输出会更干净, 小颗粒噪声被直接抹掉")
    _wait_and_close()
    return blurred


# ---------------------------------------------------------------------------
# Step 4: HSV 阈值分割
# ---------------------------------------------------------------------------
def step4_hsv_mask(blurred: np.ndarray, out_dir: Path) -> np.ndarray:
    print("\n[Step 4] HSV 阈值分割 —— inRange 生成二值 mask")
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    masked = cv2.bitwise_and(blurred, blurred, mask=mask)
    cv2.imshow("Step4 Mask (binary)", _fit(mask))
    cv2.imshow("Step4 Masked color", _fit(masked))
    cv2.imwrite(str(out_dir / "step4_mask.png"), mask)
    cv2.imwrite(str(out_dir / "step4_masked_color.png"), masked)
    fg = int((mask > 0).sum())
    print(f"  HSV 下界: {HSV_LOWER.tolist()}  上界: {HSV_UPPER.tolist()}")
    print(f"  mask 前景像素: {fg} ({fg / mask.size * 100:.2f}%)")
    _wait_and_close()
    return mask


# ---------------------------------------------------------------------------
# Step 5: 形态学开闭运算
# ---------------------------------------------------------------------------
def step5_morphology(mask: np.ndarray, out_dir: Path) -> np.ndarray:
    print("\n[Step 5] 形态学: 开运算去碎屑, 闭运算补空洞")
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    # opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

    triple = np.hstack([mask, opened, closed])
    cv2.imshow("Step5 Raw | Opened | Closed", _fit(triple))
    cv2.imwrite(str(out_dir / "step5_mask_raw.png"), mask)
    cv2.imwrite(str(out_dir / "step5_mask_opened.png"), opened)
    cv2.imwrite(str(out_dir / "step5_mask_closed.png"), closed)
    cv2.imwrite(str(out_dir / "step5_triple.png"), triple)
    print(f"  raw 前景={int((mask > 0).sum())}  opened={int((opened > 0).sum())}  closed={int((closed > 0).sum())}")
    _wait_and_close()
    return closed


# ---------------------------------------------------------------------------
# Step 6: 轮廓 + 包围盒 + 质心
# ---------------------------------------------------------------------------
def step6_contour_centroid(img: np.ndarray, clean_mask: np.ndarray, out_dir: Path) -> None:
    print("\n[Step 6] 提轮廓 -> 取最大 -> 画包围盒 + 质心")
    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("  未检测到任何轮廓, 检查 HSV 阈值"); return
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    m = cv2.moments(c)
    cx = int(m["m10"] / m["m00"]) if m["m00"] else x + w // 2
    cy = int(m["m01"] / m["m00"]) if m["m00"] else y + h // 2


    vis = img.copy()
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.drawMarker(vis, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
    cv2.imshow("Step6 Detection", _fit(vis))
    cv2.imwrite(str(out_dir / "step6_detection.png"), vis)
    print(f"  bbox=(x={x}, y={y}, w={w}, h={h})")
    print(f"  centroid=({cx}, {cy})  area={cv2.contourArea(c):.1f}")
    _wait_and_close()


# ---------------------------------------------------------------------------
# Step 7: 现场 HSV 调参 (trackbar)
# ---------------------------------------------------------------------------
def step7_tuner(image_path: Path) -> None:
    print("\n[Step 7] HSV 调参器 —— 拖滑块实时看 mask; 按 p 打印当前参数, q 退出")
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {image_path}")
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    win = "HSV Tuner"
    cv2.namedWindow(win)
    for name, init, vmax in [("H low", int(HSV_LOWER[0]), 180), ("H high", int(HSV_UPPER[0]), 180),
                              ("S low", int(HSV_LOWER[1]), 255), ("S high", int(HSV_UPPER[1]), 255),
                              ("V low", int(HSV_LOWER[2]), 255), ("V high", int(HSV_UPPER[2]), 255)]:
        cv2.createTrackbar(name, win, init, vmax, lambda _v: None)

    while True:
        hl = cv2.getTrackbarPos("H low", win); hh = cv2.getTrackbarPos("H high", win)
        sl = cv2.getTrackbarPos("S low", win); sh = cv2.getTrackbarPos("S high", win)
        vl = cv2.getTrackbarPos("V low", win); vh = cv2.getTrackbarPos("V high", win)
        mask = cv2.inRange(hsv, (hl, sl, vl), (hh, sh, vh))
        preview = cv2.bitwise_and(img, img, mask=mask)
        cv2.imshow(win, _fit(np.hstack([preview, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])))
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break
        if key == ord("p"):
            print(f"  lower=({hl},{sl},{vl})  upper=({hh},{sh},{vh})")
    cv2.destroyAllWindows()


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def run_pipeline(image_path: Path) -> None:
    out_dir = HERE / "outputs" / image_path.stem
    print(f"[pipeline] image={image_path.name}  outputs={out_dir}")
    img = step0_read_and_show(image_path, out_dir)
    step1_rgb_channels(img, out_dir)
    step2_hsv_channels(img, out_dir)
    blurred = step3_blur(img, out_dir)
    mask = step4_hsv_mask(blurred, out_dir)
    clean = step5_morphology(mask, out_dir)
    step6_contour_centroid(img, clean, out_dir)
    print("\n[pipeline] 全部 Step 完成.")


def main() -> None:
    parser = argparse.ArgumentParser(description="第十讲 OpenCV 教学脚本")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="输入图片路径")
    parser.add_argument("--tuner", action="store_true", help="只跑 HSV 调参器 (Step 7)")
    args = parser.parse_args()

    image_path = args.image if args.image.is_absolute() else (HERE / args.image).resolve()
    if args.tuner:
        step7_tuner(image_path)
    else:
        run_pipeline(image_path)


if __name__ == "__main__":
    main()
