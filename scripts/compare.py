#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对比 YOLOv8 与 YOLO11 在 HC18 上的性能：
    1. 检测指标：mAP50 / mAP50-95 / Precision / Recall / 推理速度
    2. 头围估计：以检测框拟合椭圆，换算为毫米后与官方头围真值比较 MAD / DSC / 相关系数

用法：
    python scripts/compare.py \
        --v8 runs/detect/yolov8n_hc18/weights/best.pt \
        --v11 runs/detect/yolo11n_hc18/weights/best.pt
"""

import argparse
import os
from pathlib import Path

# 解决 Windows 下多个库重复加载 OpenMP 运行库（libiomp5md.dll）的冲突
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_utils import setup_chinese_font
from ultralytics import YOLO

# 中文字体（找不到则保持默认，避免标题显示为方框）
_cn_font = setup_chinese_font()
if _cn_font:
    plt.rcParams["font.sans-serif"] = [_cn_font, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def ellipse_circumference(a, b):
    a, b = float(a), float(b)
    h = ((a - b) / (a + b)) ** 2
    return np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))


def ellipse_mask(cx, cy, a, b, angle, h, w):
    """在 (h, w) 画布上绘制实心椭圆掩膜（angle 为旋转角）。"""
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (int(round(cx)), int(round(cy))),
                (int(round(a)), int(round(b))), angle, 0, 360, 255, -1)
    return mask


def dice_coef(m1, m2):
    m1 = (m1 > 0).astype(np.uint8)
    m2 = (m2 > 0).astype(np.uint8)
    inter = int(np.logical_and(m1, m2).sum())
    total = int(m1.sum()) + int(m2.sum())
    return 2.0 * inter / total if total > 0 else 0.0


def params_count(model):
    try:
        return int(sum(p.numel() for p in model.model.parameters()))
    except Exception:
        return float("nan")


def evaluate_hc(model, val_images, gt_df, hw):
    """对验证集做推理，比较预测头围与官方真值（单位：mm）。"""
    h, w = hw
    rows = []
    for img_path in val_images:
        name = img_path.name
        gt = gt_df[gt_df["filename"] == name]
        if gt.empty:
            continue
        g = gt.iloc[0]
        res = model.predict(str(img_path), imgsz=640, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            continue
        conf = res.boxes.conf.cpu().numpy()
        xyxy = res.boxes.xyxy.cpu().numpy()
        k = int(np.argmax(conf))
        x1, y1, x2, y2 = xyxy[k]
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        a, b = (x2 - x1) / 2.0, (y2 - y1) / 2.0
        pred_hc_px = ellipse_circumference(a, b)

        gt_a, gt_b = float(g["a"]), float(g["b"])
        gt_cx, gt_cy = float(g["cx"]), float(g["cy"])
        gt_angle = float(g["angle"])
        px_size = float(g["pixel_size_mm"])
        gt_hc_mm = float(g["hc_mm"])
        pred_hc_mm = pred_hc_px * px_size if not np.isnan(px_size) else float("nan")
        dsc = dice_coef(ellipse_mask(cx, cy, a, b, 0.0, h, w),
                        ellipse_mask(gt_cx, gt_cy, gt_a, gt_b, gt_angle, h, w))
        rows.append({
            "filename": name,
            "gt_hc_mm": gt_hc_mm,
            "pred_hc_mm": pred_hc_mm,
            "gt_hc_px": float(g["hc_pixels"]),
            "pred_hc_px": pred_hc_px,
            "abs_err_mm": abs(pred_hc_mm - gt_hc_mm) if not np.isnan(pred_hc_mm) else float("nan"),
            "dsc": dsc,
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v8", required=True, help="YOLOv8 训练出的 best.pt")
    parser.add_argument("--v11", required=True, help="YOLO11 训练出的 best.pt")
    parser.add_argument("--data", default="data/dataset.yaml")
    parser.add_argument("--gt", default="data/hc_ground_truth.csv")
    parser.add_argument("--out", default="runs/comparison")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    gt_df = pd.read_csv(args.gt)
    gt_val = gt_df[gt_df["split"] == "val"].copy()

    data_dir = Path(args.data).resolve().parent
    val_images = sorted((data_dir / "yolo" / "images" / "val").glob("*.png"))
    hw = cv2.imread(str(val_images[0]), cv2.IMREAD_UNCHANGED).shape[:2]  # (h, w)

    model_paths = {"YOLOv8": args.v8, "YOLO11": args.v11}
    metrics = {}

    for mname, mpath in model_paths.items():
        print(f"\n===== {mname} 标准检测评估 =====")
        model = YOLO(mpath)
        res = model.val(data=args.data, split="val", imgsz=640, verbose=True)
        rd = res.results_dict
        speed = getattr(res, "speed", None) or {}
        metrics[mname] = {
            "mAP50": rd.get("metrics/mAP50(B)", float("nan")),
            "mAP50-95": rd.get("metrics/mAP50-95(B)", float("nan")),
            "precision": rd.get("metrics/precision(B)", float("nan")),
            "recall": rd.get("metrics/recall(B)", float("nan")),
            "inference_ms": speed.get("inference", float("nan")),
            "params": params_count(model),
            "weight_MB": os.path.getsize(mpath) / 1e6,
        }

        print(f"===== {mname} 头围估计评估 =====")
        hc_df = evaluate_hc(model, val_images, gt_val, hw)
        n = len(hc_df)
        mm = hc_df[["gt_hc_mm", "pred_hc_mm"]].dropna()
        metrics[mname].update({
            "MAD_mm": float(hc_df["abs_err_mm"].mean()) if n else float("nan"),
            "DSC": float(hc_df["dsc"].mean()) if n else float("nan"),
            "pearson_r": float(np.corrcoef(mm["gt_hc_mm"], mm["pred_hc_mm"])[0, 1])
                         if len(mm) > 1 else float("nan"),
        })
        hc_df.to_csv(out / f"hc_predictions_{mname}.csv", index=False)
        print(f"{mname}: MAD={metrics[mname]['MAD_mm']:.2f}mm, "
              f"DSC={metrics[mname]['DSC']:.4f}, r={metrics[mname]['pearson_r']:.4f}")

    summary = pd.DataFrame(metrics).T.reset_index().rename(columns={"index": "model"})
    summary.to_csv(out / "comparison_metrics.csv", index=False)
    print("\n===== 性能对比汇总 =====")
    print(summary.round(4).to_string(index=False))

    # 对比图
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    names = summary["model"].tolist()
    x = np.arange(len(names))

    axes[0, 0].bar(x - 0.2, summary["mAP50"], 0.4, label="mAP50", color="#4C72B0")
    axes[0, 0].bar(x + 0.2, summary["mAP50-95"], 0.4, label="mAP50-95", color="#55A868")
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(names)
    axes[0, 0].set_ylabel("mAP")
    axes[0, 0].set_title("检测精度对比")
    axes[0, 0].legend()

    axes[0, 1].bar(names, summary["MAD_mm"], color="#C44E52")
    axes[0, 1].set_ylabel("MAD (mm)")
    axes[0, 1].set_title("头围估计平均绝对误差")

    axes[1, 0].bar(names, summary["DSC"], color="#8172B2")
    axes[1, 0].set_ylabel("DSC")
    axes[1, 0].set_title("椭圆 Dice 相似系数")

    axes[1, 1].bar(names, summary["pearson_r"], color="#937860")
    axes[1, 1].set_ylabel("Pearson r")
    axes[1, 1].set_title("头围相关性")

    fig.tight_layout()
    fig.savefig(out / "comparison_plots.png", dpi=150)
    print(f"\n对比结果已保存到 {out}")


if __name__ == "__main__":
    main()
