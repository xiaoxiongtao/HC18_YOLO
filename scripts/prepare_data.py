#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 HC18 的掩膜标注转换为 YOLO 目标检测格式，并按病人划分训练/验证集。

输入：
    data/training_set/*_HC.png              超声图像（800x540，单通道灰度）
    data/training_set/*_HC_Annotation.png   二值掩膜（255=胎头椭圆轮廓线，0=背景）

输出：
    data/yolo/images/{train,val}/*.png      转成 3 通道的超声图像
    data/yolo/labels/{train,val}/*.txt      YOLO 格式标注（class xc yc w h，归一化）
    data/dataset.yaml                       训练配置
    data/hc_ground_truth.csv                每张图的椭圆参数、像素级头围、官方头围(mm)
"""

import argparse
import csv
import shutil
from pathlib import Path

import cv2
import numpy as np
import yaml
from sklearn.model_selection import train_test_split
from tqdm import tqdm


CLASS_ID = 0
CLASS_NAMES = {CLASS_ID: "fetal_head"}


def ellipse_circumference(a, b):
    """椭圆周长（拉马努金二阶近似），a、b 为半轴长。"""
    a, b = float(a), float(b)
    h = ((a - b) / (a + b)) ** 2
    return np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))


def extract_from_mask(mask):
    """从二值掩膜（椭圆轮廓线）提取外接框与拟合椭圆（含旋转角）。"""
    binary = (mask > 0).astype(np.uint8)
    cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return None
    cnt = max(cnts, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(cnt)
    if len(cnt) >= 5:
        (cx, cy), (major, minor), angle = cv2.fitEllipse(cnt)
        a, b = major / 2.0, minor / 2.0
    else:
        cx, cy, a, b, angle = x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0, 0.0
    return {
        "bbox": (x, y, w, h),
        "center": (cx, cy),
        "axes": (a, b),
        "angle": angle,
        "hc_pixels": ellipse_circumference(a, b),
    }


def to_yolo_label(box, img_w, img_h):
    x1, y1, w, h = box
    xc = (x1 + w / 2.0) / img_w
    yc = (y1 + h / 2.0) / img_h
    nw = w / img_w
    nh = h / img_h
    return f"{CLASS_ID} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"


def main():
    parser = argparse.ArgumentParser(description="HC18 -> YOLO 数据准备")
    parser.add_argument("--data", default="data", help="数据根目录（含 training_set / test_set）")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="验证集比例（按病人划分）")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    root = Path(args.data).resolve()
    train_dir = root / "training_set"
    yolo_dir = root / "yolo"
    dataset_yaml = root / "dataset.yaml"
    gt_csv = root / "hc_ground_truth.csv"

    assert train_dir.exists(), f"找不到训练集目录：{train_dir}"

    # 读取官方像素尺寸(mm/px)与头围真值(mm)
    pixel_file = root / "training_set_pixel_size_and_HC.csv"
    pixel_info = {}
    if pixel_file.exists():
        with open(pixel_file, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    pixel_info[row["filename"]] = (
                        float(row["pixel size(mm)"]),
                        float(row["head circumference (mm)"]),
                    )
                except (KeyError, ValueError):
                    continue
        print(f"已读取官方像素尺寸与头围真值：{len(pixel_info)} 张")
    else:
        print(f"未找到 {pixel_file.name}，头围将仅以像素为单位")

    # 收集图像与掩膜
    images = sorted(train_dir.glob("*HC.png"))
    images = [p for p in images if "Annotation" not in p.name]
    masks = {p.name.replace("_Annotation.png", ".png"): p
             for p in train_dir.glob("*_Annotation.png")}

    print(f"找到 {len(images)} 张训练图像，{len(masks)} 张掩膜")

    # 按病人划分（前缀数字为病人 ID，避免同一病人的多张图泄漏到训练/验证两端）
    def patient_of(name):
        return name.split("_")[0]

    patients = sorted({patient_of(p.name) for p in images})
    train_patients, val_patients = train_test_split(
        patients, test_size=args.val_ratio, random_state=args.seed
    )
    val_patients = set(val_patients)
    print(f"病人总数 {len(patients)}，训练病人 {len(patients) - len(val_patients)}，"
          f"验证病人 {len(val_patients)}")

    # 重建输出目录
    if yolo_dir.exists():
        shutil.rmtree(yolo_dir)
    for split in ("train", "val"):
        (yolo_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (yolo_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    gt_rows = []
    n_train = 0
    n_val = 0
    for img_path in tqdm(images, desc="转换标注"):
        name = img_path.name
        mask_path = masks.get(name)
        if mask_path is None:
            print(f"警告：缺少掩膜 {name}")
            continue

        img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_UNCHANGED)
        h, w = img.shape[:2]

        info = extract_from_mask(mask)
        if info is None:
            print(f"警告：空掩膜 {name}")
            continue

        split = "train" if patient_of(name) in train_patients else "val"
        if split == "train":
            n_train += 1
        else:
            n_val += 1

        # 保存 3 通道图像（灰度复制为 BGR，保证 YOLO 默认 3 通道输入）
        if img.ndim == 2:
            img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img_bgr = img
        cv2.imwrite(str(yolo_dir / "images" / split / name), img_bgr)

        # 写 YOLO 标签
        label = to_yolo_label(info["bbox"], w, h)
        label_path = yolo_dir / "labels" / split / (name.replace(".png", ".txt"))
        label_path.write_text(label + "\n")

        x1, y1, bw, bh = info["bbox"]
        cx, cy = info["center"]
        a, b = info["axes"]
        px_size, hc_mm = pixel_info.get(name, (float("nan"), float("nan")))
        gt_rows.append({
            "filename": name,
            "patient": patient_of(name),
            "split": split,
            "x": x1, "y": y1, "w": bw, "h": bh,
            "cx": round(cx, 2), "cy": round(cy, 2),
            "a": round(a, 2), "b": round(b, 2), "angle": round(info["angle"], 2),
            "hc_pixels": round(info["hc_pixels"], 2),
            "pixel_size_mm": px_size,
            "hc_mm": hc_mm,
        })

    # 写 GT 头围 CSV
    fieldnames = ["filename", "patient", "split", "x", "y", "w", "h",
                  "cx", "cy", "a", "b", "angle", "hc_pixels",
                  "pixel_size_mm", "hc_mm"]
    with open(gt_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(gt_rows)

    # 写 dataset.yaml
    dataset = {
        "path": str(root).replace("\\", "/"),
        "train": "yolo/images/train",
        "val": "yolo/images/val",
        "names": {CLASS_ID: CLASS_NAMES[CLASS_ID]},
    }
    with open(dataset_yaml, "w") as f:
        yaml.safe_dump(dataset, f, sort_keys=False, allow_unicode=True)

    print(f"完成：训练 {n_train} 张，验证 {n_val} 张")
    print(f"dataset.yaml -> {dataset_yaml}")
    print(f"头围真值 CSV -> {gt_csv}")


if __name__ == "__main__":
    main()
