# -*- coding: utf-8 -*-
"""生成课件所需的网络架构 / 检测头 / 损失函数 / 样本分配示意图（matplotlib 绘制）。"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, PathPatch
from matplotlib.path import Path

try:  # matplotlib >= 3.11 移除了 FancyBBoxPatch，这里自行实现圆角矩形
    from matplotlib.patches import Circle  # noqa: F401
except ImportError:  # pragma: no cover
    from matplotlib.patches import Ellipse as _Ellipse

    class Circle(_Ellipse):
        def __init__(self, xy, radius, **kw):
            kw.pop("radius", None)
            super().__init__(xy, radius * 2, radius * 2, **kw)


def _rounded_path(x, y, w, h, r):
    r = min(r, w / 2.0, h / 2.0)
    verts = [(x + r, y), (x + w - r, y), (x + w, y), (x + w, y + r),
             (x + w, y + h - r), (x + w, y + h), (x + w - r, y + h),
             (x + r, y + h), (x, y + h), (x, y + h - r),
             (x, y + r), (x, y), (x + r, y), (x + r, y)]
    codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3,
             Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO,
             Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3,
             Path.CURVE3, Path.CLOSEPOLY]
    return Path(verts, codes)


def rbox(ax, x, y, w, h, fc="none", ec="black", lw=1.2, r=0.012, ls=None, zorder=3):
    p = PathPatch(_rounded_path(x, y, w, h, r), facecolor=fc, edgecolor=ec,
                  linewidth=lw, linestyle=ls, zorder=zorder)
    ax.add_patch(p)
    return p

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from plot_utils import setup_chinese_font

CN = setup_chinese_font()
if CN:
    plt.rcParams["font.sans-serif"] = [CN, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

DEEP = "#0E3F8C"; BLUE = "#1E4FA8"; MID = "#3D7BD9"
LIGHT = "#E8EFF8"; LIGHT2 = "#F0F5FC"; RED = "#D9534F"
TXT = "#1A2230"; SUB = "#4A5568"; GRAY = "#8B97A8"; ORANGE = "#E08A2E"


def box(ax, x, y, w, h, text, fc, ec=None, fs=9.5, tc="white", lw=1.2, pad=0.012,
        bold=False, style=None):
    ec = ec or fc
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, r=min(0.014, h / 3.0), zorder=3)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight=weight, zorder=4, linespacing=1.35)


def arrow(ax, x1, y1, x2, y2, color=MID, lw=1.6, style="-|>", ls="-", rad=0.0, zorder=2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=13, color=color, linewidth=lw,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=zorder))


def label(ax, x, y, text, fs=9, color=SUB, ha="center", va="center", bold=False, zorder=5):
    ax.text(x, y, text, ha=ha, va=va, color=color, fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=zorder, linespacing=1.3)


def blank(ax, xlim=(0, 1), ylim=(0, 1)):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.axis("off")
    ax.set_aspect("auto")


# ---------------------------------------------------------------- 图1：整体架构
def fig_arch():
    fig, ax = plt.subplots(figsize=(15.0, 7.4), dpi=170)
    blank(ax)

    # 分区底纹
    for (x, w, t, c) in [(0.035, 0.20, "Backbone 主干网络", DEEP),
                         (0.255, 0.40, "Neck 特征融合（FPN + PAN）", BLUE),
                         (0.675, 0.155, "Head 检测头", MID),
                         (0.845, 0.13, "后处理", RED)]:
        rbox(ax, x, 0.045, w, 0.90, fc=LIGHT2, ec=c, lw=1.4, r=0.012, ls=(0, (5, 2)), zorder=1)
        ax.text(x + w / 2, 0.905, t, ha="center", va="center", color=c,
                fontsize=11.5, fontweight="bold", zorder=5,
                bbox=dict(fc="white", ec="none", pad=2.2))

    # 输入
    box(ax, 0.055, 0.795, 0.16, 0.10, "输入图像\n640 × 640 × 3", LIGHT, DEEP, fs=10, tc=DEEP, bold=True)
    arrow(ax, 0.135, 0.79, 0.135, 0.735, DEEP, 1.8)

    # Backbone 五层
    bb = [
        ("Conv 3×3 / s=2", "320 × 320", "P1 / 2", "16"),
        ("Conv 3×3 / s=2", "160 × 160", "P2 / 4", "32"),
        ("C2f（v8） / C3k2（v11）", "80 × 80", "P3 / 8", "64"),
        ("C2f（v8） / C3k2（v11）", "40 × 40", "P4 / 16", "128"),
        ("SPPF  +  C2PSA（仅 v11）", "20 × 20", "P5 / 32", "256"),
    ]
    y = 0.655
    for mod, size, pid, ch in bb:
        box(ax, 0.055, y, 0.16, 0.10, f"{mod}\n{size}", BLUE if "SPPF" not in mod else DEEP, fs=9)
        label(ax, 0.235, y + 0.05, f"{pid}\n{ch} ch", fs=8.5, color=SUB)
        if y > 0.235:
            arrow(ax, 0.135, y + 0.002, 0.135, y - 0.027, MID, 1.5)
        y -= 0.125
    label(ax, 0.135, 0.115, "逐级下采样：分辨率减半 · 通道加倍", fs=8.5, color=GRAY)

    # ---- Neck：三行轨道 + 上/下行汇聚 ----
    rows = [(0.66, "P3", "80²"), (0.44, "P4", "40²"), (0.22, "P5", "20²")]
    for yc, pn, size in rows:
        box(ax, 0.268, yc - 0.038, 0.052, 0.076, f"{pn}\n{size}", "white", BLUE, fs=8.5, tc=DEEP)
        ax.add_patch(Circle((0.348, yc), 0.017, fc="white", ec=BLUE, lw=1.6, zorder=4))
        label(ax, 0.348, yc, "+", fs=9, color=BLUE, bold=True)
        box(ax, 0.386, yc - 0.05, 0.104, 0.10, "C2f / C3k2\n特征融合", BLUE, fs=8.8)
        box(ax, 0.516, yc - 0.038, 0.056, 0.076, f"{pn}\nout", MID, fs=8.5)
        arrow(ax, 0.320, yc, 0.332, yc, BLUE, 1.4)
        arrow(ax, 0.365, yc, 0.384, yc, BLUE, 1.4)
        arrow(ax, 0.490, yc, 0.514, yc, BLUE, 1.4)
    # FPN 自顶向下（红实线）
    arrow(ax, 0.294, 0.262, 0.342, 0.420, RED, 1.7)
    arrow(ax, 0.438, 0.492, 0.354, 0.640, RED, 1.7)
    # PAN 自底向上（蓝虚线）
    arrow(ax, 0.544, 0.618, 0.354, 0.462, MID, 1.7, ls="--")
    arrow(ax, 0.544, 0.398, 0.354, 0.242, MID, 1.7, ls="--")
    label(ax, 0.455, 0.115,
          "红实线：FPN 自顶向下（语义 → 细节）    蓝虚线：PAN 自底向上（细节 → 语义）    +：拼接 Concat",
          fs=8.8, color=SUB)

    # ---- Head ----
    heads = [(0.66, "Detect · P3", "80 × 80 × 65 · 小目标"),
             (0.44, "Detect · P4", "40 × 40 × 65 · 中目标"),
             (0.22, "Detect · P5", "20 × 20 × 65 · 大目标")]
    for yc, t, sub in heads:
        box(ax, 0.695, yc - 0.042, 0.118, 0.084, f"{t}\n{sub}", MID, fs=8.5)
        arrow(ax, 0.574, yc, 0.693, yc, MID, 1.5)

    # ---- 后处理 ----
    arrow(ax, 0.815, 0.52, 0.858, 0.47, RED, 1.5)
    arrow(ax, 0.815, 0.44, 0.858, 0.44, RED, 1.5)
    arrow(ax, 0.815, 0.30, 0.858, 0.41, RED, 1.5)
    box(ax, 0.862, 0.36, 0.10, 0.16, "解码 8400 框\n置信度过滤\n→ NMS\n→ 检测框", RED, fs=8.5, bold=True)
    label(ax, 0.912, 0.245, "fetal_head\n(x, y, w, h, conf)", fs=8.5, color=RED, bold=True)

    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, "arch_full.png"), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("arch_full.png")


# ---------------------------------------------------------------- 图2：检测头
def fig_head():
    fig, ax = plt.subplots(figsize=(13.4, 5.6), dpi=170)
    blank(ax)

    box(ax, 0.02, 0.36, 0.115, 0.24, "融合特征\n80 × 80 × 64", LIGHT, DEEP, fs=9.5, tc=DEEP, bold=True)
    arrow(ax, 0.137, 0.48, 0.185, 0.48, MID, 1.7)

    # 回归分支
    box(ax, 0.19, 0.62, 0.115, 0.14, "回归分支\nConv 3×3 ×2", BLUE, fs=9)
    arrow(ax, 0.307, 0.69, 0.35, 0.69, BLUE, 1.6)
    box(ax, 0.353, 0.635, 0.115, 0.11, "1×1 Conv\n4 × 16 通道", BLUE, fs=8.8)
    arrow(ax, 0.47, 0.69, 0.512, 0.69, BLUE, 1.6)
    box(ax, 0.515, 0.635, 0.115, 0.11, "DFL\n16 桶 → 期望", MID, fs=8.8)
    arrow(ax, 0.632, 0.69, 0.672, 0.69, MID, 1.6)
    box(ax, 0.675, 0.635, 0.115, 0.11, "四边距离\n(l, t, r, b)", DEEP, fs=8.8)
    arrow(ax, 0.792, 0.69, 0.83, 0.69, DEEP, 1.6)
    box(ax, 0.833, 0.635, 0.10, 0.11, "→ 框\nxyxy", LIGHT, DEEP, fs=9, tc=DEEP)

    # 分类分支
    box(ax, 0.19, 0.12, 0.115, 0.14, "分类分支\nConv 3×3 ×2", ORANGE, fs=9)
    arrow(ax, 0.307, 0.19, 0.35, 0.19, ORANGE, 1.6)
    box(ax, 0.353, 0.145, 0.115, 0.11, "1×1 Conv\n1 通道（nc=1）", ORANGE, fs=8.8)
    arrow(ax, 0.47, 0.19, 0.512, 0.19, ORANGE, 1.6)
    box(ax, 0.515, 0.145, 0.115, 0.11, "Sigmoid\n类别概率", ORANGE, fs=8.8)
    arrow(ax, 0.632, 0.19, 0.672, 0.19, ORANGE, 1.6)
    box(ax, 0.675, 0.145, 0.115, 0.11, "置信度\nconf", ORANGE, fs=8.8)

    label(ax, 0.19, 0.86, "解耦头 Decoupled Head：分类与回归各走一条分支，互不干扰", fs=10.5, color=DEEP, bold=True, ha="left")
    label(ax, 0.02, 0.86, "", fs=9)

    # 右侧 Anchor-Free 示意
    rbox(ax, 0.80, 0.10, 0.18, 0.40, fc=LIGHT2, ec=MID, lw=1.3, r=0.012, zorder=2)
    label(ax, 0.89, 0.465, "Anchor-Free 直接回归", fs=9.5, color=DEEP, bold=True)
    # 网格点与目标框示意
    gx, gy, gw, gh = 0.835, 0.155, 0.11, 0.235
    ax.add_patch(plt.Rectangle((gx, gy), gw, gh, fc="white", ec=DEEP, lw=1.5, zorder=3))
    px, py = gx + gw * 0.42, gy + gh * 0.45
    ax.plot([px], [py], "o", color=RED, ms=7, zorder=5)
    arrow(ax, px, py, gx, py, RED, 1.3, style="-|>", zorder=4)
    arrow(ax, px, py, gx + gw, py, RED, 1.3, style="-|>", zorder=4)
    arrow(ax, px, py, px, gy + gh, RED, 1.3, style="-|>", zorder=4)
    arrow(ax, px, py, px, gy, RED, 1.3, style="-|>", zorder=4)
    label(ax, gx - 0.012, py, "l", fs=8.5, color=RED)
    label(ax, gx + gw + 0.012, py, "r", fs=8.5, color=RED)
    label(ax, px, gy - 0.018, "b", fs=8.5, color=RED)
    label(ax, px, gy + gh + 0.018, "t", fs=8.5, color=RED)
    label(ax, 0.89, 0.125, "每个网格点预测到四边的距离\n无需预设锚框尺寸", fs=8.5, color=SUB)

    label(ax, 0.67, 0.86, "· 本项目 nc = 1（胎儿头部 single class）\n· 每锚点输出 4×16 + 1 = 65 个数值",
          fs=9, color=SUB, ha="left")

    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, "head_detail.png"), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("head_detail.png")


# ---------------------------------------------------------------- 图3：损失函数
def fig_loss():
    fig, ax = plt.subplots(figsize=(13.4, 5.9), dpi=170)
    blank(ax)

    # 顶部总公式
    rbox(ax, 0.02, 0.80, 0.96, 0.16, fc=DEEP, ec="none", lw=0, r=0.015, zorder=3)
    ax.text(0.5, 0.885, "L  =  7.5 · L_box  +  1.5 · L_dfl  +  0.5 · L_cls",
            ha="center", va="center", color="white", fontsize=17, fontweight="bold", zorder=4)
    ax.text(0.5, 0.835, "总损失 = 框回归 + 分布焦点 + 分类（权重取自本项目 args.yaml：box=7.5 · dfl=1.5 · cls=0.5）",
            ha="center", va="center", color="#C7D8F5", fontsize=9.5, zorder=4)

    # 三项卡片
    items = [
        (0.02, BLUE, "L_box · 权重 7.5", "框回归损失 = 1 − CIoU",
         "CIoU = IoU − ρ²(b, b_gt) / c² − α·v\nv = (4/π²)(arctan w_gt/h_gt − arctan w/h)²",
         "同时惩罚重叠面积 / 中心距离 / 宽高比\n—— 决定框能否贴住颅骨边缘"),
        (0.35, MID, "L_dfl · 权重 1.5", "分布焦点损失 DFL",
         "DFL(S_i, S_i+1) = −[(y_i+1 − y)·log S_i\n+ (y − y_i)·log S_i+1]",
         "把“到边的距离”看成 16 个区间的概率分布\n用期望求距离 —— 让边界回归更精细"),
        (0.68, ORANGE, "L_cls · 权重 0.5", "分类损失 BCE",
         "BCE = −[ y·log p + (1 − y)·log(1 − p) ]",
         "本项目仅胎儿头部一类（nc = 1）\n分类容易收敛，故权重最低"),
    ]
    for x, c, title, sub, formula, note in items:
        rbox(ax, x, 0.26, 0.30, 0.50, fc=LIGHT2, ec=c, lw=1.6, r=0.014, zorder=3)
        ax.text(x + 0.15, 0.72, title, ha="center", va="center", color=c,
                fontsize=11.5, fontweight="bold", zorder=4)
        ax.text(x + 0.15, 0.67, sub, ha="center", va="center", color=TXT, fontsize=10, zorder=4)
        ax.text(x + 0.15, 0.575, formula, ha="center", va="center", color=DEEP,
                fontsize=9.5, zorder=4, linespacing=1.5,
                bbox=dict(fc="white", ec=c, lw=1.0, pad=5, boxstyle="round,pad=0.3,rounding_size=0.05"))
        ax.text(x + 0.15, 0.33, note, ha="center", va="center", color=SUB,
                fontsize=9, zorder=4, linespacing=1.45)

    # 底部权重条
    ax.text(0.02, 0.24, "损失权重分配（Ultralytics 默认，本项目沿用）", ha="left", va="center",
            color=DEEP, fontsize=10.5, fontweight="bold")
    bars = [("L_box", 7.5, BLUE), ("L_dfl", 1.5, MID), ("L_cls", 0.5, ORANGE)]
    yy = 0.18
    for name, val, c in bars:
        ax.text(0.02, yy + 0.018, name, ha="left", va="center", color=TXT, fontsize=9.5)
        ax.add_patch(plt.Rectangle((0.10, yy), val / 7.5 * 0.55, 0.036, fc=c, ec="none", zorder=3))
        ax.text(0.10 + val / 7.5 * 0.55 + 0.012, yy + 0.018, f"{val}", ha="left", va="center",
                color=c, fontsize=9.5, fontweight="bold")
        yy -= 0.055
    ax.text(0.72, 0.155, "框回归权重最高（7.5），\n因为头围测量依赖框的\n边界精度——框差 1 px，\n头围就差约 0.07 mm。",
            ha="left", va="center", color=SUB, fontsize=9, linespacing=1.5,
            bbox=dict(fc=LIGHT, ec="none", pad=5, boxstyle="round,pad=0.3,rounding_size=0.05"))

    ax.text(0.5, 0.045, "注：三项损失只对被分配为正样本的锚点计算（负样本仅参与分类损失）",
            ha="center", va="center", color=GRAY, fontsize=9)

    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, "loss_func.png"), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("loss_func.png")


# ---------------------------------------------------------------- 图4：样本分配与后处理
def fig_assign():
    fig, ax = plt.subplots(figsize=(13.4, 5.4), dpi=170)
    blank(ax)

    # 训练流程
    rbox(ax, 0.02, 0.55, 0.96, 0.36, fc=LIGHT2, ec=BLUE, lw=1.4, r=0.014, ls=(0, (5, 2)), zorder=1)
    ax.text(0.05, 0.875, "训练时：正样本怎么分配？", ha="left", va="center", color=BLUE,
            fontsize=11.5, fontweight="bold")

    steps = [(0.045, "8 400 个锚点\n80²+40²+20²", LIGHT, DEEP),
             (0.235, "TAL 对齐度打分\nt = s^α · u^β", BLUE, "white"),
             (0.425, "每个真值框\n取 Top-10 锚点", MID, "white"),
             (0.615, "正样本\nL_box + L_dfl + L_cls", DEEP, "white"),
             (0.80, "负样本\n仅 L_cls", LIGHT, DEEP)]
    for i, (x, t, fc, tc) in enumerate(steps):
        w = 0.16
        box(ax, x, 0.63, w, 0.19, t, fc if fc != LIGHT else "white",
            DEEP if fc == LIGHT else fc, fs=9.5, tc=tc if fc != LIGHT else DEEP)
        if i < len(steps) - 1:
            arrow(ax, x + w + 0.004, 0.725, x + w + 0.035, 0.725, MID, 1.6)
    ax.text(0.5, 0.585, "s = 类别置信度    u = 预测框与真值框的 IoU    α、β 控制两者权重（Ultralytics 默认 topk=10）",
            ha="center", va="center", color=SUB, fontsize=9)

    # 推理流程
    rbox(ax, 0.02, 0.08, 0.96, 0.38, fc="#FDF2F2", ec=RED, lw=1.4, r=0.014, ls=(0, (5, 2)), zorder=1)
    ax.text(0.05, 0.425, "推理时：成千上万个框怎么变成 1 个？", ha="left", va="center", color=RED,
            fontsize=11.5, fontweight="bold")

    steps2 = [(0.045, "8 400 个\n候选框", "white", DEEP),
              (0.235, "置信度过滤\nconf > 0.25", RED, "white"),
              (0.425, "按类别 NMS\nIoU 阈值 0.7", RED, "white"),
              (0.615, "最多保留\nmax_det = 300", RED, "white"),
              (0.80, "输出胎儿头部框\n→ 拟合椭圆 → 头围", DEEP, "white")]
    for i, (x, t, fc, tc) in enumerate(steps2):
        w = 0.16
        box(ax, x, 0.16, w, 0.20, t, fc, DEEP if fc == "white" else fc, fs=9.5,
            tc=tc if fc != "white" else DEEP)
        if i < len(steps2) - 1:
            arrow(ax, x + w + 0.004, 0.26, x + w + 0.035, 0.26, RED, 1.6)
    ax.text(0.5, 0.115, "本项目为单类检测，NMS 后每张图通常只剩 1 个高置信框；conf / IoU / max_det 均取自 args.yaml",
            ha="center", va="center", color=SUB, fontsize=9)

    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, "assign_nms.png"), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("assign_nms.png")


if __name__ == "__main__":
    fig_arch(); fig_head(); fig_loss(); fig_assign()
