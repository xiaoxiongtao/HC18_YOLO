#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用同一套超参数分别训练 YOLOv8 与 YOLO11，保证性能对比公平。

用法示例：
    python scripts/train.py --model yolov8n.pt --epochs 100
    python scripts/train.py --model yolo11n.pt --epochs 100
"""

import argparse
import os

# 解决 Windows 下 torch / numpy(MKL) 重复加载 OpenMP 运行库（libiomp5md.dll）导致的冲突
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="训练 YOLOv8 / YOLO11 胎儿头围检测")
    parser.add_argument("--model", default="yolo11n.pt",
                        help="预训练权重：yolov8n.pt / yolo11n.pt / yolov8s.pt / yolo11s.pt ...")
    parser.add_argument("--data", default="data/dataset.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="", help="留空自动选择；如 0 或 cpu")
    parser.add_argument("--project", default="", help="输出子目录名（留空即保存到 runs/detect/<name>）")
    parser.add_argument("--name", default=None, help="输出目录名，默认由模型名自动生成")
    parser.add_argument("--patience", type=int, default=20, help="早停轮数")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    # Windows 下多进程 DataLoader 偶发异常，默认取 0 更稳妥
    workers = args.workers if args.workers is not None else (0 if os.name == "nt" else 8)
    name = args.name or f"{os.path.splitext(os.path.basename(args.model))[0]}_hc18"

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device or None,
        project=args.project,
        name=name,
        patience=args.patience,
        seed=args.seed,
        workers=workers,
        verbose=True,
    )


if __name__ == "__main__":
    main()
