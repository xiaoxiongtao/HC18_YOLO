#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
课堂任务：用训练好的 YOLO 模型，对官方测试集完成一次完整的“头围自动测量”。

任务流程（对应课件 PART 04）：
    ① 推理：加载 best.pt，对 data/test_set 中的图像预测胎儿头部框
    ② 测量：框中心/半轴 → 拉马努金椭圆周长 → × 像素尺寸 → 头围（mm）
    ③ 检查：头围分布直方图 + 可视化样张，人工核对是否合理

用法：
    python scripts/class_task.py \
        --model runs/detect/yolo11n_hc18/weights/best.pt \
        --num 20 --out runs/class_task

参数 --num 控制处理张数（默认 20；--num 0 表示全部 335 张）。
"""

import argparse
import os
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_utils import setup_chinese_font
from ultralytics import YOLO

_cn_font = setup_chinese_font()
if _cn_font:
    plt.rcParams["font.sans-serif"] = [_cn_font, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def ellipse_circumference(a, b):
    """拉马努金二阶近似椭圆周长（prepare_data.py / compare.py 同款实现）。"""
    a, b = float(a), float(b)
    h = ((a - b) / (a + b)) ** 2
    return np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))


def draw_result(img_bgr, box_xyxy, conf, hc_mm):
    """在图上画检测框、内切椭圆与头围文本。"""
    out = img_bgr.copy()
    x1, y1, x2, y2 = [int(round(v)) for v in box_xyxy]
    cv2.rectangle(out, (x1, y1), (x2, y2), (217, 83, 79), 2)
    cv2.ellipse(out, ((x1 + x2) // 2, (y1 + y2) // 2),
                ((x2 - x1) // 2, (y2 - y1) // 2), 0, 0, 360, (61, 123, 217), 2)
    text = f"HC = {hc_mm:.1f} mm  (conf {conf:.2f})"
    cv2.putText(out, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                (14, 63, 140), 2, cv2.LINE_AA)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="训练得到的 best.pt 路径")
    parser.add_argument("--test-dir", default="data/test_set")
    parser.add_argument("--pixel-csv", default="data/test_set_pixel_size.csv")
    parser.add_argument("--num", type=int, default=20,
                        help="处理前 N 张（0 = 全部 335 张）")
    parser.add_argument("--out", default="runs/class_task")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    px_df = pd.read_csv(args.pixel_csv)
    px_df.columns = ["filename", "pixel_size_mm"]
    px_map = dict(zip(px_df["filename"], px_df["pixel_size_mm"]))

    test_dir = Path(args.test_dir)
    images = sorted(test_dir.glob("*_HC.png"))
    if args.num > 0:
        images = images[: args.num]
    print(f"任务开始：模型 {args.model} · 待处理 {len(images)} 张")

    model = YOLO(args.model)
    rows, vis_samples = [], []
    for img_path in images:
        img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        h, w = img.shape[:2]
        res = model.predict(str(img_path), imgsz=640, conf=0.25, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            rows.append({"filename": img_path.name, "status": "未检出"})
            continue
        k = int(np.argmax(res.boxes.conf.cpu().numpy()))
        conf = float(res.boxes.conf.cpu().numpy()[k])
        x1, y1, x2, y2 = res.boxes.xyxy.cpu().numpy()[k]
        a, b = (x2 - x1) / 2.0, (y2 - y1) / 2.0          # 半轴（像素）
        hc_px = ellipse_circumference(a, b)
        px_mm = px_map.get(img_path.name)
        hc_mm = hc_px * px_mm if px_mm else float("nan")
        rows.append({
            "filename": img_path.name,
            "status": "OK",
            "conf": round(conf, 4),
            "a_px": round(a, 2), "b_px": round(b, 2),
            "hc_px": round(hc_px, 2),
            "pixel_size_mm": px_mm,
            "hc_mm": round(hc_mm, 2) if px_mm else float("nan"),
        })
        if len(vis_samples) < 6:
            vis_samples.append(draw_result(cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                                           if img.ndim == 2 else img,
                                           (x1, y1, x2, y2), conf, hc_mm))

    df = pd.DataFrame(rows)
    df.to_csv(out / "task_predictions.csv", index=False)
    print(f"逐图结果已保存：{out / 'task_predictions.csv'}")

    ok = df[df["status"] == "OK"]
    miss = df[df["status"] != "OK"]
    print("\n===== 结果统计 =====")
    print(f"检出 {len(ok)} / {len(df)}（未检出 {len(miss)} 张）")
    if len(ok):
        print(f"头围范围：{ok['hc_mm'].min():.1f} – {ok['hc_mm'].max():.1f} mm，"
              f"均值 {ok['hc_mm'].mean():.1f} mm，中位数 {ok['hc_mm'].median():.1f} mm")
        print(f"最低置信度：{ok['conf'].min():.3f}")

        # 头围分布直方图
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.hist(ok["hc_mm"], bins=20, color="#3D7BD9", edgecolor="white")
        ax.axvline(ok["hc_mm"].median(), color="#D9534F", ls="--", lw=1.5,
                   label=f"中位数 {ok['hc_mm'].median():.0f} mm")
        ax.set_xlabel("预测头围 (mm)"); ax.set_ylabel("图像数")
        ax.set_title(f"测试集前 {len(ok)} 张预测头围分布")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / "hc_distribution.png", dpi=150)
        plt.close(fig)

        # 可视化样张（2 × 3）
        if vis_samples:
            fig, axes = plt.subplots(2, 3, figsize=(12, 7))
            for ax_i, im in zip(axes.ravel(), vis_samples):
                ax_i.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
                ax_i.axis("off")
            fig.suptitle("检测结果可视化：红框 = YOLO 检测框，蓝椭圆 = 拟合椭圆", fontsize=13)
            fig.tight_layout()
            fig.savefig(out / "vis_samples.png", dpi=150)
            plt.close(fig)

    print(f"\n可视化已保存：{out / 'hc_distribution.png'} · {out / 'vis_samples.png'}")
    print("任务完成。请对照结果思考：误差可能来自哪里？（提示：检测框 → 正圆假设 vs 真实椭圆姿态）")


if __name__ == "__main__":
    main()
