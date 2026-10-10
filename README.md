# 胎儿头围（HC18）检测 —— YOLOv8 vs YOLO11

基于 HC18 挑战赛数据的胎儿头围（Head Circumference, HC）目标检测项目。使用 **YOLOv8** 与 **YOLO11** 分别训练，比较两者的检测精度（mAP）、头围估计误差（MAD / DSC）等指标，并通过 Jupyter Notebook 展示数据、标注与预测结果的可视化。

> **作者**：肖雄涛

## 1. 数据集

- **名称**：HC18（Automated Measurement of Fetal Head Circumference，ISBI 2018 挑战赛）
- **来源**：Zenodo — https://zenodo.org/records/1327317
- **内容**：标准平面二维产前超声扫描数据，用于测量胎儿头围。图像覆盖不同孕龄、解剖结构、图像质量和超声伪影。
  - 训练集 `data/training_set/`：**999** 张 800×540 灰度图像，每张配有一张二值掩膜标注 `*_HC_Annotation.png`（白色=胎头椭圆**轮廓线**，黑色=背景）。部分病人含多张扫描（文件名带 `_2HC` / `_3HC` / `_4HC` 后缀）。
  - 测试集 `data/test_set/`：**335** 张 800×540 灰度图像，**无标注**（仅用于推理演示）。
- **像素尺寸与官方头围**：HC18 官方提供每张图的像素尺寸（mm/px）与头围真值（mm），见 `data/training_set_pixel_size_and_HC.csv`（训练集）和 `data/test_set_pixel_size.csv`（测试集）。本项目用它们把预测头围换算为**毫米**，并与官方头围真值比较。

## 2. 环境安装

```bash
# 建议使用虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

> 注意：`requirements.txt` 中的 `torch` 默认从 PyPI 安装 CPU 版。如需 GPU 加速，请先按 [pytorch.org](https://pytorch.org/get-started/locally/) 安装匹配 CUDA 版本的 torch/torchvision，再执行 `pip install -r requirements.txt`。

## 3. 项目结构

```
HC18/
├── data/
│   ├── training_set/           # 999 张训练图像 + 掩膜（原始数据）
│   ├── test_set/               # 335 张测试图像（无标注）
│   ├── dataset.yaml            # 训练配置（由 prepare_data.py 生成）
│   ├── hc_ground_truth.csv     # 真实头围 / 椭圆参数（由 prepare_data.py 生成）
│   └── yolo/                   # YOLO 格式数据集（由 prepare_data.py 生成）
│       ├── images/{train,val}/
│       └── labels/{train,val}/
├── scripts/
│   ├── prepare_data.py         # 掩膜 → YOLO 标注 + 划分数据集
│   ├── train.py                # 训练 YOLOv8 / YOLO11
│   └── compare.py              # 性能对比
├── notebooks/
│   └── hc18_report.ipynb       # 数据介绍 + 标注 + 结果可视化
├── runs/                       # 训练 / 评估输出（自动生成）
├── README.md
└── requirements.txt
```

## 4. 数据预处理（掩膜 → YOLO 标注）

HC18 提供的是像素级椭圆掩膜，而 YOLO 目标检测需要边界框。`scripts/prepare_data.py` 完成：

1. 读取二值掩膜，用 `cv2.fitEllipse` 拟合椭圆，取掩膜外接矩形作为检测框；
2. 生成 YOLO 格式标签 `class x_center y_center width height`（均为归一化值）；
3. 灰度图复制为 3 通道，写入 `data/yolo/`；
4. 按病人划分训练 / 验证集（默认 8:2，避免同一病人的多张图泄漏到两端）；
5. 拟合椭圆周长作为像素级头围，并合并官方像素尺寸与头围真值（mm），一并保存到 `data/hc_ground_truth.csv`。

```bash
python scripts/prepare_data.py
```

## 5. 训练

`scripts/train.py` 对两个模型使用**完全相同的超参数**，保证对比公平：

```bash
# YOLOv8（nano）
python scripts/train.py --model yolov8n.pt --epochs 100

# YOLO11（nano）
python scripts/train.py --model yolo11n.pt --epochs 100
```

可选参数：更换模型规模（`yolov8s.pt` / `yolo11s.pt`）、调整 `--imgsz`、`--batch`、`--device 0`（指定 GPU）、`--epochs` 等。训练结果默认保存在 `runs/detect/<model>_hc18/`。

## 6. 性能对比

```bash
python scripts/compare.py \
    --v8 runs/detect/yolov8n_hc18/weights/best.pt \
    --v11 runs/detect/yolo11n_hc18/weights/best.pt
```

输出到 `runs/comparison/`：

- `comparison_metrics.csv`：mAP50、mAP50-95、Precision、Recall、推理速度、参数量、MAD、DSC、Pearson r
- `comparison_plots.png`：检测精度 / 头围误差 / Dice / 相关性对比柱状图
- `hc_predictions_*.csv`：逐图头围预测结果

### 评价指标说明

| 指标 | 含义 |
| --- | --- |
| mAP50 / mAP50-95 | 检测框质量（IoU 阈值 0.5 / 0.5–0.95 平均） |
| MAD（平均绝对误差） | 预测头围与官方头围真值的平均绝对差（毫米） |
| DSC（Dice 相似系数） | 预测椭圆与真实椭圆区域的重叠程度 |
| Pearson r | 预测头围与真实头围的线性相关性 |

## 7. Jupyter Notebook

`notebooks/hc18_report.ipynb` 包含：

1. 数据介绍与统计；
2. 标注说明（掩膜 → 椭圆 → 检测框）；
3. 数据预处理与 YOLO 格式转换；
4. 训练过程回顾；
5. 导入训练好的权重进行结果可视化（验证集 + 测试集）；
6. YOLOv8 与 YOLO11 性能对比。

```bash
jupyter notebook notebooks/hc18_report.ipynb
```

> 未训练时，Notebook 仍可完整运行数据介绍 / 标注 / 预处理部分；可视化与对比部分会在检测到缺少 `best.pt` 时给出提示。

## 8. 主要依赖

见 `requirements.txt`。

## 9. 作者与版权

- **作者**：肖雄涛
- **版权**：Copyright © 2026 肖雄涛，保留所有权利。
- **用途许可**：本项目（含代码、训练脚本与结果）仅供**学习、教学、科研等非商业用途**使用，**禁止用于任何商业目的**；未经作者书面许可，不得将本项目用于商业用途，或进行销售、再分发、商业部署。
- **数据版权**：HC18 数据集版权归其原作者与发布机构所有，使用请遵守数据源（Zenodo: https://zenodo.org/records/1327317 ）的相关许可与引用要求。
