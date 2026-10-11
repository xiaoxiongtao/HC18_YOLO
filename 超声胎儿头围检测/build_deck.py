# -*- coding: utf-8 -*-
"""《超声胎儿头围检测》教学课件构建脚本（python-pptx 兜底实现）。"""
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from lxml import etree

EMU_PX = 9525
DEEP = "0E3F8C"; BLUE = "1E4FA8"; MID = "3D7BD9"
LIGHT = "E8EFF8"; LIGHT2 = "F0F5FC"; BG2 = "F7F9FC"
RED = "D9534F"; TXT = "1A2230"; SUB = "4A5568"; GRAY = "8B97A8"
LINE = "D6DCE5"; WHITE = "FFFFFF"
FONT = "Microsoft YaHei"

prs = Presentation()
prs.slide_width = 12192000
prs.slide_height = 6858000
BLANK = prs.slide_layouts[6]


def E(px):
    return int(px * EMU_PX)


def _set_run(run, text, size, color, bold, italic=False, font=FONT):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", font)


def T(slide, x, y, w, h, paras, size=18, color=TXT, bold=False,
      align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, leading=1.15):
    """paras: 字符串，或 [(text, overrides), ...] 列表（多段落为列表的列表）。"""
    tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    if isinstance(paras, str):
        paras = [[(paras, {})]]
    first = True
    for para in paras:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if isinstance(para, str):
            para = [(para, {})]
        elif isinstance(para, tuple):
            para = [para]
        elif isinstance(para, list) and para and isinstance(para[0], str):
            para = [(para[0], {})]
        p.alignment = align
        p.line_spacing = leading
        for text, ov in para:
            r = p.add_run()
            _set_run(r, text, ov.get("size", size), ov.get("color", color),
                     ov.get("bold", bold), ov.get("italic", False), ov.get("font", FONT))
    return tb


def R(slide, x, y, w, h, fill=None, line=None, lw=1.0, round_=None, alpha=None):
    st = MSO_SHAPE.ROUNDED_RECTANGLE if round_ is not None else MSO_SHAPE.RECTANGLE
    sp = slide.shapes.add_shape(st, E(x), E(y), E(w), E(h))
    if round_ is not None:
        try:
            sp.adjustments[0] = round_
        except Exception:
            pass
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = RGBColor.from_string(fill)
        if alpha is not None:
            clr = sp.fill.fore_color._xFill.find(qn("a:srgbClr"))
            a = etree.SubElement(clr, qn("a:alpha"))
            a.set("val", str(int(alpha * 1000)))
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = RGBColor.from_string(line)
        sp.line.width = Pt(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def IMG(slide, path, x, y, w, h):
    return slide.shapes.add_picture(path, E(x), E(y), E(w), E(h))


def ARROW(slide, x, y, w, h, color=MID):
    sp = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, E(x), E(y), E(w), E(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = RGBColor.from_string(color)
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def header(slide, chapter, pageno=None):
    R(slide, 0, 0, 1280, 72, fill=DEEP)
    T(slide, 40, 0, 600, 72, "超声胎儿头围检测 · 教学课件",
      size=16, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    T(slide, 640, 0, 600, 72, chapter, size=16, color=WHITE,
      align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    T(slide, 40, 96, 8, 34, "", size=1)  # spacer noop
    R(slide, 40, 100, 8, 32, fill=BLUE, round_=0.3)
    T(slide, 1040, 668, 200, 20, _auto_pageno(), size=15, color=BLUE, bold=True,
      align=PP_ALIGN.RIGHT)
    T(slide, 40, 668, 600, 20, "HC18 胎儿头围检测项目 · 肖雄涛", size=14, color=GRAY)


def title_row(slide, title, sub=""):
    R(slide, 40, 100, 8, 32, fill=BLUE, round_=0.3)
    if sub:
        T(slide, 62, 92, 1050, 48, [(title, {}), ("  " + sub, {"size": 16, "color": GRAY, "bold": False})],
          size=30, color=DEEP, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    else:
        T(slide, 62, 92, 1100, 48, title, size=30, color=DEEP, bold=True,
          anchor=MSO_ANCHOR.MIDDLE)


def top_bar(slide):
    R(slide, 0, 0, 1280, 14, fill=DEEP)


def pageno_only(slide, pageno=None, white=False):
    T(slide, 1040, 668, 200, 20, _auto_pageno(), size=15,
      color=WHITE if white else BLUE, bold=True, align=PP_ALIGN.RIGHT)


def card(slide, x, y, w, h, title, body, tsize=22, bsize=18,
         fill=LIGHT2, tcolor=DEEP, bcolor=SUB):
    R(slide, x, y, w, h, fill=fill, line=LINE, lw=1, round_=0.06)
    T(slide, x + 20, y + 14, w - 40, 34, title, size=tsize, color=tcolor, bold=True)
    T(slide, x + 20, y + 52, w - 40, max(h - 64, 10), body, size=bsize, color=bcolor, leading=1.35)


def strip(slide, x, y, w, h, text, fill=LIGHT, color=DEEP, size=19):
    R(slide, x, y, w, h, fill=fill, round_=0.12)
    T(slide, x + 24, y, w - 48, h, text, size=size, color=color,
      anchor=MSO_ANCHOR.MIDDLE, leading=1.25)


def rich_strip(slide, x, y, w, h, paras, fill=LIGHT, size=19, color=DEEP):
    R(slide, x, y, w, h, fill=fill, round_=0.12)
    T(slide, x + 24, y, w - 48, h, paras, size=size, color=color,
      anchor=MSO_ANCHOR.MIDDLE, leading=1.25)


A = "assets/"
TOTAL_SLIDES = 27


def _auto_pageno():
    """按 add_slide 顺序自动生成页码（当前 slide 已加入 prs.slides）。"""
    return "%02d / %d" % (len(prs.slides), TOTAL_SLIDES)

# ============ 01 封面 ============
s = prs.slides.add_slide(BLANK)
IMG(s, A + "sample_image.png", 840, 0, 440, 720)
R(s, 840, 0, 440, 720, fill=DEEP, alpha=0.30)
R(s, 840, 620, 440, 100, fill=DEEP, alpha=0.72)
T(s, 840, 636, 420, 80, "HC18 标准平面产前超声图像（800×540 灰度）",
  size=13, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
R(s, 0, 0, 1280, 14, fill=DEEP)
T(s, 64, 130, 680, 30, "医学影像人工智能 · 教学课件", size=20, color=MID)
T(s, 64, 168, 760, 100, "超声胎儿头围检测", size=54, color=DEEP, bold=True)
T(s, 64, 288, 700, 30, [("Automated Measurement of Fetal Head Circumference", {"italic": True})],
  size=20, color=SUB)
R(s, 64, 336, 110, 6, fill=BLUE, round_=0.5)
T(s, 64, 366, 700, 40, "基于 YOLOv8 与 YOLO11 的目标检测实践", size=26, color=TXT, bold=True)
T(s, 64, 414, 700, 70, ["从 HC18 挑战赛数据到头围自动估计的全流程：",
                        "数据 · 标注转换 · 网络架构 · 训练 · 评估"],
  size=18, color=SUB, leading=1.5)
chips = ["汇报人：肖雄涛", "2026 年 10 月", "数据：HC18 · ISBI 2018"]
cx = 64
for c in chips:
    w = 44 + len(c) * 16
    R(s, cx, 596, w, 44, fill=LIGHT, round_=0.5)
    T(s, cx, 596, w, 44, c, size=16, color=DEEP, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cx += w + 14

# ============ 02 目录 ============
s = prs.slides.add_slide(BLANK)
R(s, 0, 0, 340, 720, fill=DEEP)
T(s, 48, 120, 260, 70, "目 录", size=48, color=WHITE, bold=True)
T(s, 48, 196, 260, 30, "CONTENTS", size=17, color=WHITE)
R(s, 48, 240, 56, 5, fill=MID, round_=0.5)
T(s, 48, 272, 240, 160, ["五章内容，跟随一个真实的", "深度学习项目，完成从", "临床问题到课堂任务的", "完整闭环。"],
  size=15, color=WHITE, leading=1.8)
T(s, 48, 620, 240, 24, "HC18 · 胎儿头围检测", size=13, color=WHITE)
items = [
    ("01", "临床背景与数据", "头围测量的临床意义 · HC18 数据集构成与统计"),
    ("02", "方法与技术路线", "标注转换 · YOLO 架构逐层精讲 · 损失函数 · 训练与评估"),
    ("03", "实验与结果分析", "训练曲线 · YOLOv8 vs YOLO11 性能对比 · 头围估计精度"),
    ("04", "课堂任务", "用 best.pt 对测试集完成一次完整的头围自动测量"),
    ("05", "总结与展望", "项目结论 · 后续改进方向"),
]
iy = 72
for num, t1, t2 in items:
    R(s, 410, iy, 810, 96, fill=BG2, line=LINE, lw=1, round_=0.12)
    R(s, 438, iy + 22, 52, 52, fill=BLUE, round_=0.18)
    T(s, 438, iy + 22, 52, 52, num, size=22, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 514, iy + 16, 680, 34, t1, size=22, color=TXT, bold=True)
    T(s, 514, iy + 54, 680, 28, t2, size=14, color=SUB)
    iy += 120
pageno_only(s, "02 / 27")

# ============ 03 章节扉页01 ============
def section_slide(num, part, title, bullets, img, caption, pageno=None):
    s = prs.slides.add_slide(BLANK)
    top_bar(s)
    T(s, 50, 40, 500, 260, num, size=200, color=LIGHT, bold=True)
    T(s, 64, 290, 640, 30, part, size=19, color=MID, bold=True)
    T(s, 64, 322, 680, 70, title, size=44, color=DEEP, bold=True)
    R(s, 64, 404, 90, 6, fill=BLUE, round_=0.5)
    by = 432
    for b in bullets:
        R(s, 64, by + 8, 10, 10, fill=BLUE, round_=0.5)
        T(s, 90, by, 620, 40, b, size=19, color=TXT)
        by += 40
    IMG(s, img, 790, 200, 430, 287)
    R(s, 790, 200, 430, 287, fill=None, line=LINE, lw=1)
    T(s, 790, 496, 430, 24, caption, size=13, color=GRAY, align=PP_ALIGN.CENTER)
    pageno_only(s, pageno)
    return s

section_slide("01", "PART 01", "临床背景与数据",
              ["为什么头围（HC）是产前超声的核心测量指标",
               "HC18 挑战赛数据集：999 训练 + 335 测试图像",
               "像素尺寸与头围真值：评价以毫米为单位进行"],
              A + "sample_image.png", "标准平面二维产前超声扫描", "03 / 19")

# ============ 04 临床意义 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 1 章 · 临床背景与数据", "04 / 19")
title_row(s, "胎儿头围：产前超声评估的关键指标", "Head Circumference")
IMG(s, A + "sample_image.png", 40, 156, 560, 378)
R(s, 40, 156, 560, 378, fill=None, line=LINE, lw=1)
T(s, 40, 542, 560, 22, "HC18 训练样例 002_HC.png：胎头呈类椭圆回声结构", size=13, color=GRAY)
cards4 = [
    ("1", "发育监测的核心参数", "头围（HC）反映胎儿脑发育情况，与双顶径、股骨长共同构成产前生长评估体系，用于核对孕周、筛查小头畸形与巨头等生长异常。", BLUE),
    ("2", "测量依赖标准平面", "规范测法要求在丘脑平面获取胎头横切面，沿颅骨外缘描绘椭圆并读取周长——平面的获取与描迹都依赖医师经验。", BLUE),
    ("3", "人工测量的局限", "手动描迹存在操作者间差异，大样本筛查耗时耗力。用深度学习自动定位胎头并估计头围，可同时提升效率与一致性。", RED),
]
cy = 156
for num, t1, b1, cc in cards4:
    R(s, 624, cy, 616, 130, fill=LIGHT2, line=LINE, lw=1, round_=0.1)
    R(s, 644, cy + 16, 30, 30, fill=cc, round_=0.25)
    T(s, 644, cy + 16, 30, 30, num, size=14, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 686, cy + 14, 540, 32, t1, size=20, color=DEEP, bold=True)
    T(s, 644, cy + 52, 576, 70, b1, size=15, color=SUB, leading=1.3)
    cy += 144
rich_strip(s, 40, 592, 1200, 54,
           [[("本章问题：", {"bold": True}), ("能否让模型像医师一样，从一张超声图像中自动找到胎头并算出头围？", {})]],
           size=19)

# ============ 05 HC18 数据集 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 1 章 · 临床背景与数据", "05 / 19")
title_row(s, "HC18 数据集：ISBI 2018 挑战赛", "来源：Zenodo · records/1327317")
kpis = [("999", "训练图像（含掩膜标注）"), ("335", "测试图像（无标注）"), ("806", "位病人（部分含多次扫描）")]
kx = 40
for num, lab in kpis:
    R(s, kx, 156, 194, 150, fill=LIGHT2, line=LINE, lw=1, round_=0.1)
    T(s, kx + 18, 168, 160, 76, num, size=48, color=BLUE, bold=True)
    T(s, kx + 18, 250, 164, 46, lab, size=12, color=SUB, leading=1.2)
    kx += 213
R(s, 40, 322, 620, 158, fill=WHITE, line=LINE, lw=1, round_=0.08)
T(s, 60, 338, 580, 30, "数据规格与官方真值", size=19, color=DEEP, bold=True)
T(s, 60, 372, 580, 100, ["· 800×540 单通道灰度超声图像",
                         "· 官方提供每张图的像素尺寸 0.049–0.393 mm/px",
                         "· 头围真值范围 44.3 – 346.4 mm（均值 174.4 mm）",
                         "· 覆盖不同孕龄、图像质量与超声伪影"], size=14, color=SUB, leading=1.35)
R(s, 40, 496, 620, 110, fill=LIGHT, line=LINE, lw=1, round_=0.08)
T(s, 60, 508, 580, 90,
  [[("关键设计：", {"bold": True}),
    ("按病人而非按图像划分训练 / 验证集（793 / 206），避免同一病人的多张扫描同时出现在两端，造成数据泄漏与虚高的评估结果。", {})]],
  size=14, color=DEEP, leading=1.4)
IMG(s, A + "labels_yolo11.jpg", 700, 156, 400, 400)
R(s, 700, 156, 400, 400, fill=None, line=LINE, lw=1)
T(s, 700, 564, 400, 40, "训练集检测框分布：目标居中、宽高强相关（类椭圆）",
  size=13, color=GRAY, align=PP_ALIGN.CENTER)

# ============ 06 章节扉页02 ============
section_slide("02", "PART 02", "方法与技术路线",
              ["技术路线总览：从掩膜标注到毫米级头围",
               "数据预处理：椭圆拟合与 YOLO 标签生成",
               "YOLO 网络架构与统一超参数训练",
               "评价指标：检测精度 + 头围测量误差"],
              A + "sample_mask.png", "HC18 官方标注：胎头椭圆轮廓线掩膜", "06 / 19")

# ============ 07 技术路线 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线", "07 / 19")
title_row(s, "技术路线：从掩膜标注到毫米级头围")
flow = [("① 掩膜标注", "读取二值掩膜", "白色像素为轮廓线"),
        ("② 椭圆拟合", "cv2.fitEllipse", "得中心 / 半轴 / 角度"),
        ("③ YOLO 标签", "外接矩形归一化", "class xc yc w h"),
        ("④ 训练对比", "同一超参数训练", "YOLOv8 / YOLO11"),
        ("⑤ 头围估计", "椭圆周长 × 像素尺寸", "换算为毫米")]
fx = 40
for i, (t1, l1, l2) in enumerate(flow):
    fillc = DEEP if i == 4 else BLUE
    R(s, fx, 170, 200, 84, fill=fillc, round_=0.16)
    T(s, fx, 170, 200, 84, t1, size=19, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, fx, 264, 200, 56, [l1, l2], size=14, color=SUB,
      align=PP_ALIGN.CENTER, leading=1.3)
    if i < 4:
        ARROW(s, fx + 208, 196, 34, 32)
    fx += 242
mods = [("prepare_data.py", "掩膜 → YOLO 标注转换、灰度图复制为 3 通道、按病人 8:2 划分训练 / 验证集。"),
        ("train.py", "封装 Ultralytics YOLO 训练接口，两个模型共享同一套超参数与数据。"),
        ("compare.py", "统一评估：检测指标 + 头围误差（MAD / DSC / 相关性）+ 对比图输出。")]
mx = 40
for t1, b1 in mods:
    card(s, mx, 384, 386, 132, t1, b1, tsize=19, bsize=14)
    mx += 407
rich_strip(s, 40, 540, 1200, 62,
           [[("关键产物：", {"bold": True}),
             ("data/yolo/（图像 + 标签）· dataset.yaml（训练配置）· hc_ground_truth.csv（头围真值）· runs/comparison/（指标与逐图预测）", {})]],
           size=16)

# ============ 08 数据预处理 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线", "08 / 19")
title_row(s, "数据预处理：掩膜轮廓 → YOLO 边界框")
IMG(s, A + "sample_image.png", 40, 156, 342, 231)
R(s, 40, 156, 342, 231, fill=None, line=LINE, lw=1)
T(s, 40, 392, 342, 24, "① 原始超声图像（800×540 灰度）", size=13, color=SUB, align=PP_ALIGN.CENTER)
IMG(s, A + "sample_mask.png", 398, 156, 342, 231)
R(s, 398, 156, 342, 231, fill=None, line=LINE, lw=1)
T(s, 398, 392, 342, 24, "② 二值掩膜（白色 = 椭圆轮廓线）", size=13, color=SUB, align=PP_ALIGN.CENTER)
R(s, 40, 428, 700, 216, fill=LIGHT2, line=LINE, lw=1, round_=0.08)
R(s, 150, 462, 340, 120, fill=None, line=BLUE, lw=2.5)
ov = s.shapes.add_shape(MSO_SHAPE.OVAL, E(168), E(486), E(304), E(72))
ov.fill.solid(); ov.fill.fore_color.rgb = RGBColor.from_string(MID)
ov.fill.fore_color._xFill.find(qn("a:srgbClr"))
clr = ov.fill.fore_color._xFill.find(qn("a:srgbClr"))
a = etree.SubElement(clr, qn("a:alpha")); a.set("val", "20000")
ov.line.color.rgb = RGBColor.from_string(MID); ov.line.width = Pt(2)
ov.rotation = 348
ov.shadow.inherit = False
R(s, 317, 518, 8, 8, fill=RED, round_=0.5)
T(s, 336, 486, 240, 22, "拟合椭圆中心 (cx, cy)", size=12, color=RED)
T(s, 150, 440, 340, 20, "外接矩形 = 检测框 (x, y, w, h)", size=12, color=BLUE)
T(s, 400, 588, 330, 20, "半轴 a, b → 椭圆周长 = 头围", size=12, color=DEEP)
T(s, 40, 610, 700, 22, "③ 几何换算：框用于训练，椭圆用于测量头围", size=13, color=GRAY)
card(s, 756, 156, 484, 126, "处理流程",
     "findContours 提轮廓 → boundingRect 得外接框 → fitEllipse 得中心 / 半轴 / 角度 → 灰度复制 3 通道 → 按病人 8:2 划分。",
     tsize=17, bsize=13)
R(s, 756, 294, 484, 142, fill=LIGHT2, line=LINE, lw=1, round_=0.08)
T(s, 776, 306, 444, 28, "椭圆周长（拉马努金二阶近似）", size=17, color=DEEP, bold=True)
T(s, 776, 340, 444, 58, ["HC = π(a+b) · [1 + 3h / (10 + √(4−3h))]", "h = ((a−b)/(a+b))²"],
  size=16, color=TXT, leading=1.5)
T(s, 776, 404, 444, 22, "a、b 为椭圆半轴长，出自 prepare_data.py 源码", size=11, color=GRAY)
R(s, 756, 448, 484, 126, fill=DEEP, round_=0.08)
T(s, 776, 460, 444, 28, "YOLO 标签示例", size=17, color=WHITE, bold=True)
T(s, 776, 492, 444, 52, [("0 0.504375 0.412037", {"font": "Consolas"}), ("    0.283750 0.331481", {"font": "Consolas"})],
  size=15, color=WHITE, leading=1.4)
T(s, 776, 546, 444, 22, "class x_center y_center width height（归一化）", size=11, color=WHITE)

# ============ 09 网络架构总览 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "YOLO 网络架构总览：一图看懂数据流", "YOLOv8 / YOLO11 同源结构")
IMG(s, A + "arch_full.png", 128, 148, 1024, 490)
R(s, 128, 148, 1024, 490, fill=None, line=LINE, lw=1)
T(s, 40, 644, 1200, 22,
  "整体数据流：Backbone 五级下采样提特征 → FPN + PAN 双向融合 → 三尺度解耦头 → 解码与 NMS（示意图，通道按 n 规模标注）",
  size=13, color=GRAY, align=PP_ALIGN.CENTER)

# ============ 10 Backbone 详解 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "Backbone：特征是怎么一层层提炼的")
# 左侧：五级下采样结构表
layers10 = [
    ("层级", "模块", "输出尺寸", "作用"),
    ("P1 / 2", "Conv 3×3, s=2", "320 × 320", "第一次降采样，保边缘细节"),
    ("P2 / 4", "Conv 3×3, s=2", "160 × 160", "降采样 + 扩通道"),
    ("P3 / 8", "C2f（v8）/ C3k2（v11）", "80 × 80", "开始输出到检测头（小目标）"),
    ("P4 / 16", "C2f（v8）/ C3k2（v11）", "40 × 40", "中层语义（中目标）"),
    ("P5 / 32", "SPPF（+ C2PSA 仅 v11）", "20 × 20", "深层语义 + 多尺度感受野"),
]
tbl_shape = s.shapes.add_table(len(layers10), 4, E(40), E(156), E(700), E(288))
tbl = tbl_shape.table
for ci, wd in enumerate([90, 240, 120, 250]):
    tbl.columns[ci].width = E(wd)
for ri, row in enumerate(layers10):
    tbl.rows[ri].height = E(46)
    for ci, val in enumerate(row):
        c = tbl.cell(ri, ci)
        c.margin_left = E(8); c.margin_right = E(8)
        c.margin_top = E(2); c.margin_bottom = E(2)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor.from_string(BLUE if ri == 0 else (WHITE if ri % 2 else BG2))
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if ci < 3 else PP_ALIGN.LEFT
        r = p.add_run()
        _set_run(r, val, 12.5 if ri else 14, WHITE if ri == 0 else TXT, ri == 0 or ci == 0)
T(s, 40, 450, 700, 22, "尺寸按 640 输入计算；通道数经 n 规模宽度系数缩放（16 → 256）", size=12, color=GRAY)
# 左下：三个关键模块卡（紧凑版）
mods10 = [
    ("Conv（卷积）", "Conv2d + BN + SiLU；s=2 时分辨率减半、通道翻倍，是网络“压缩—抽象”的基本步。"),
    ("C2f / C3k2（特征块）", "多分支梯度流结构，兼顾精度与速度；YOLO11 用 C3k2 替代 C2f，更轻量。"),
    ("SPPF / C2PSA", "SPPF 串联最大池化拓宽感受野；C2PSA 是 YOLO11 新增的空间注意力模块。"),
]
my = 478
for t1, b1 in mods10:
    R(s, 40, my, 700, 54, fill=LIGHT2, line=LINE, lw=1, round_=0.12)
    T(s, 60, my + 5, 660, 22, t1, size=14, color=DEEP, bold=True)
    T(s, 60, my + 27, 660, 24, b1, size=11.5, color=SUB, leading=1.15)
    my += 59
# 右侧：讲解要点
R(s, 776, 156, 464, 168, fill=DEEP, round_=0.08)
T(s, 800, 172, 416, 30, "为什么逐级下采样？", size=19, color=WHITE, bold=True)
T(s, 800, 210, 416, 100,
  ["· 分辨率减半 → 计算可控，感受野更大",
   "· 通道加倍 → 语义表达更丰富",
   "· 浅层记边缘纹理，深层记结构语义"],
  size=13.5, color=WHITE, leading=1.5)
R(s, 776, 340, 464, 146, fill=LIGHT2, line=LINE, lw=1, round_=0.08)
T(s, 800, 354, 416, 28, "感受野与本任务的关系", size=18, color=DEEP, bold=True)
T(s, 800, 388, 416, 90,
  "胎头在图中占比较大（多在 1/3 以上），P4 / P5 尺度即可覆盖；但小孕周胎头偏小，P3 尺度不可或缺——三尺度都要保留。",
  size=13.5, color=SUB, leading=1.4)
R(s, 776, 502, 464, 130, fill=LIGHT, round_=0.08)
T(s, 800, 514, 416, 28, "课堂提问", size=18, color=DEEP, bold=True)
T(s, 800, 548, 416, 76,
  "如果把 SPPF 去掉会怎样？——大小胎头尺寸差异大，单一感受野容易“看不全”或“看太散”，mAP 对尺度会更敏感。",
  size=13.5, color=SUB, leading=1.4)

# ============ 11 Neck 详解 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "Neck：FPN + PAN 双向特征融合")
# 上半：两条流程带
fpn = ["P5 深层语义", "上采样 ×2", "与 P4 拼接", "融合块", "上采样 ×2", "与 P3 拼接", "融合块 → P3"]
pan = ["P3 细节特征", "下采样 ×2", "与 P4 拼接", "融合块", "下采样 ×2", "与 P5 拼接", "融合块 → P5"]
for iy2, name, steps, c1 in [(156, "FPN\n自顶向下", fpn, BLUE), (296, "PAN\n自底向上", pan, MID)]:
    R(s, 40, iy2, 1200, 116, fill=BG2, line=LINE, lw=1, round_=0.06)
    R(s, 56, iy2 + 18, 132, 80, fill=c1, round_=0.12)
    T(s, 56, iy2 + 18, 132, 80, name, size=17, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    sx = 210
    sw = (1200 - 210 - 40 - 6 * 26) / 7
    for i, st in enumerate(steps):
        R(s, sx, iy2 + 34, sw, 48, fill=LIGHT, round_=0.18)
        T(s, sx, iy2 + 34, sw, 48, st, size=13, color=DEEP,
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 6:
            ARROW(s, sx + sw + 4, iy2 + 48, 20, 20)
        sx += sw + 26
# 下半：为什么需要融合 + 三尺度职责
cards11 = [
    ("为什么要双向融合？", "深层特征“知道是什么”但位置粗；浅层特征“知道在哪”但语义弱。FPN 把语义送下去，PAN 把定位细节送上来，两头都强。"),
    ("三个尺度的分工", "P3（80²）看小目标 · P4（40²）看中目标 · P5（20²）看大目标。三个检测头并行，谁的尺度合适谁来负责。"),
    ("对本项目的意义", "胎头大小随孕周变化极大（HC 44–346 mm），多尺度融合正是模型能同时框住小孕周与足月胎头的关键。"),
]
cx = 40
for t1, b1 in cards11:
    card(s, cx, 440, 386, 148, t1, b1, tsize=18, bsize=14)
    cx += 407
rich_strip(s, 40, 608, 1200, 46,
           [[("一句话：", {"bold": True}),
             ("Neck 是“翻译官”——把主干里的信息重新组织成三个尺度、语义与定位兼备的特征图，交给检测头。", {})]],
           size=17)

# ============ 12 检测头详解 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "Head：Anchor-Free 解耦头怎么出框", "以 P3 尺度为例")
IMG(s, A + "head_detail.png", 40, 150, 1200, 501)
R(s, 40, 150, 1200, 501, fill=None, line=LINE, lw=1)
T(s, 40, 658, 1200, 20,
  "分类与回归各走一条分支；Anchor-Free 直接回归到四边的距离，经 DFL 求期望得到坐标（nc=1，每锚点 65 个数值）",
  size=13, color=GRAY, align=PP_ALIGN.CENTER)

# ============ 13 损失函数 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "损失函数：模型靠什么学会“框得准”", "权重取自本项目 args.yaml")
IMG(s, A + "loss_func.png", 72, 150, 1136, 500)
R(s, 72, 150, 1136, 500, fill=None, line=LINE, lw=1)
T(s, 40, 656, 1200, 20,
  "训练日志中 box_loss / dfl_loss / cls_loss 三条曲线即对应这三项（见第 18 页训练曲线）",
  size=12.5, color=GRAY, align=PP_ALIGN.CENTER)

# ============ 14 样本分配与后处理 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线")
title_row(s, "正样本分配与推理后处理", "TAL Assigner · NMS")
IMG(s, A + "assign_nms.png", 70, 150, 1141, 460)
R(s, 70, 150, 1141, 460, fill=None, line=LINE, lw=1)
rich_strip(s, 40, 618, 1200, 48,
           [[("教学要点：", {"bold": True}),
             ("训练看 TAL（谁算回归损失），推理看 NMS（谁留下来）——conf 0.25 · IoU 0.7 · max_det 300 均取自本项目 args.yaml。", {})]],
           size=15)

# ============ 10 训练配置 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线", "10 / 19")
title_row(s, "训练配置：同一套超参数的公平对比")
R(s, 40, 156, 360, 484, fill=DEEP, round_=0.08)
T(s, 66, 180, 310, 40, "公平对比原则", size=24, color=WHITE, bold=True)
R(s, 66, 228, 60, 5, fill=MID, round_=0.5)
T(s, 66, 248, 310, 130,
  "两个模型使用完全相同的数据划分与超参数，仅主干网络不同。这样性能差异才能归因于架构本身，而非训练技巧。",
  size=15, color=WHITE, leading=1.5)
R(s, 66, 400, 310, 74, fill=WHITE, alpha=0.12, round_=0.15)
T(s, 82, 410, 280, 56, [[("YOLOv8n：", {"bold": True}), ("早停于 68 轮，", {})], ["训练用时约 32.8 分钟"]],
  size=14, color=WHITE, leading=1.35)
R(s, 66, 490, 310, 74, fill=WHITE, alpha=0.12, round_=0.15)
T(s, 82, 500, 280, 56, [[("YOLO11n：", {"bold": True}), ("早停于 60 轮，", {})], ["训练用时约 30.4 分钟"]],
  size=14, color=WHITE, leading=1.35)
rows10 = [
    ("超参数", "取值", "说明"),
    ("epochs / patience", "100 / 20", "最多 100 轮，20 轮无提升则早停"),
    ("imgsz / batch", "640 / 16", "标准输入尺寸与批大小"),
    ("lr0 / momentum", "0.01 / 0.937", "初始学习率与动量"),
    ("weight_decay", "0.0005", "权重衰减正则"),
    ("数据增强", "Mosaic + HSV + 翻转", "scale 0.5 · fliplr 0.5 · hsv 增强"),
    ("seed", "42", "固定随机种子，结果可复现"),
    ("数据划分", "793 / 206（按病人 8:2）", "避免同一病人跨集泄漏"),
]
tbl_shape = s.shapes.add_table(len(rows10), 3, E(424), E(156), E(816), E(420))
tbl = tbl_shape.table
tbl.columns[0].width = E(240)
tbl.columns[1].width = E(250)
tbl.columns[2].width = E(326)
for ri, row in enumerate(rows10):
    tbl.rows[ri].height = E(52)
    for ci, val in enumerate(row):
        c = tbl.cell(ri, ci)
        c.margin_left = E(10); c.margin_right = E(10)
        c.margin_top = E(4); c.margin_bottom = E(4)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor.from_string(BLUE if ri == 0 else (WHITE if ri % 2 else BG2))
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if ci < 2 else PP_ALIGN.LEFT
        r = p.add_run()
        _set_run(r, val, 14 if ri else 15, WHITE if ri == 0 else TXT, ri == 0 or ci == 0)
T(s, 424, 590, 816, 22, "摘自 runs/detect/*/args.yaml，两个模型配置完全一致", size=12, color=GRAY)

# ============ 11 评价指标 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 2 章 · 方法与技术路线", "11 / 19")
title_row(s, "评价指标：从“检测得准”到“量得准”")
metrics = [
    ("检测指标", "mAP50 / mAP50-95",
     "IoU 阈值 0.5 及 0.5–0.95 区间平均的平均精度，衡量检测框定位与质量。",
     "本项目：mAP50 = 0.995，mAP50-95 ≈ 0.95。"),
    ("测量误差", "MAD（平均绝对误差）",
     "预测头围与官方真值的平均绝对差，单位毫米，是临床最关心的指标。",
     "本项目：YOLOv8 2.03 mm · YOLO11 2.39 mm。"),
    ("形状重叠", "DSC（Dice 相似系数）",
     "预测椭圆与真实椭圆区域的重叠程度，反映胎头形状还原质量。",
     "本项目：两模型均 ≈ 0.97。"),
    ("相关性", "Pearson r",
     "预测头围与真值头围的线性相关系数，检查是否存在系统性偏差。",
     "本项目：r ≈ 0.999，接近完全线性。"),
]
pos = [(40, 160), (640, 160), (40, 366), (640, 366)]
for (tag, name, body, num), (mx, my) in zip(metrics, pos):
    R(s, mx, my, 600, 190, fill=LIGHT2, line=LINE, lw=1, round_=0.08)
    R(s, mx + 20, my + 18, 84, 30, fill=BLUE if tag == "检测指标" else DEEP, round_=0.4)
    T(s, mx + 20, my + 18, 84, 30, tag, size=13, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, mx + 118, my + 14, 470, 36, name, size=20, color=DEEP, bold=True)
    T(s, mx + 20, my + 60, 560, 66, body, size=15, color=SUB, leading=1.35)
    T(s, mx + 20, my + 136, 560, 40, num, size=15, color=DEEP, bold=True, leading=1.3)
rich_strip(s, 40, 576, 1200, 60,
           [[("教学要点：", {"bold": True}),
             ("检测指标好 ≠ 测量误差小。评价医学测量任务，必须同时看“框得准不准”和“量得准不准”两类指标。", {})]],
           size=17)

# ============ 12 章节扉页03 ============
section_slide("03", "PART 03", "实验与结果分析",
              ["训练过程：损失收敛与精度爬升",
               "性能对比：mAP、参数量与推理速度",
               "头围精度：MAD 2.0–2.4 mm，r ≈ 0.999",
               "结果可视化：验证集与困难样本表现"],
              A + "comparison_plots.png", "两模型四项指标对比总览（compare.py 输出）", "12 / 19")

# ============ 13 训练曲线 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 3 章 · 实验与结果分析", "13 / 19")
title_row(s, "训练过程：损失收敛与精度爬升", "YOLO11n 训练曲线（results.png）")
IMG(s, A + "results_yolo11.png", 40, 160, 730, 394)
R(s, 40, 160, 730, 394, fill=None, line=LINE, lw=1)
T(s, 40, 562, 730, 22, "左列：训练损失（box / cls / dfl）；右列：验证精度（P / R / mAP50 / mAP50-95）",
  size=12, color=GRAY)
ins13 = [("① 损失快速收敛", "三类损失约 10 轮内陡降并趋平稳，验证损失无回升——未出现过拟合。"),
         ("② 精度迅速到位", "mAP50 约 10 轮即达 0.99+，最终 0.995；Precision / Recall 双双逼近 1.0。"),
         ("③ 瓶颈在高 IoU 区间", "mAP50-95 从 0.87 缓升至 0.95——框的边界精细度才是继续提升的方向。")]
iy = 160
for t1, b1 in ins13:
    card(s, 794, iy, 446, 122, t1, b1, tsize=18, bsize=14)
    iy += 134
rich_strip(s, 40, 596, 1200, 56,
           [[("解读：", {"bold": True}),
             ("单类、大目标、形态规律的检测任务相对容易；mAP50-95 的缓慢爬升提示后续应关注椭圆边界的精细回归。", {})]],
           size=17)

# ============ 14 性能对比 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 3 章 · 实验与结果分析", "14 / 19")
title_row(s, "检测性能对比：YOLOv8 vs YOLO11")
model_cards = [
    ("0.995", "YOLOv8n · mAP50", "mAP50-95 0.955 · 参数 3.14M · 6.49 MB · 1.88 ms"),
    ("0.995", "YOLO11n · mAP50", "mAP50-95 0.952 · 参数 2.60M · 5.49 MB · 2.38 ms"),
]
mx = 40
for num, t1, sub in model_cards:
    R(s, mx, 156, 590, 108, fill=LIGHT2, line=LINE, lw=1, round_=0.1)
    T(s, mx + 24, 156, 190, 108, num, size=48, color=BLUE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    T(s, mx + 214, 172, 360, 34, t1, size=20, color=DEEP, bold=True)
    T(s, mx + 214, 210, 360, 40, sub, size=13, color=SUB, leading=1.25)
    mx += 610
rows14 = [
    ("指标", "YOLOv8n", "YOLO11n", "解读"),
    ("mAP50", "0.995", "0.995", "两模型检测精度持平"),
    ("mAP50-95", "0.955", "0.952", "高 IoU 区间 v8 略占优"),
    ("Precision / Recall", "0.990 / 1.000", "0.994 / 1.000", "验证集全部正确检出"),
    ("参数量 / 权重体积", "3.14M / 6.49 MB", "2.60M / 5.49 MB", "YOLO11 少约 17% 参数"),
    ("推理时延", "1.88 ms", "2.38 ms", "v8 推理更快"),
]
tbl_shape = s.shapes.add_table(len(rows14), 4, E(40), E(284), E(1200), E(280))
tbl = tbl_shape.table
for ci, wd in enumerate([260, 260, 260, 420]):
    tbl.columns[ci].width = E(wd)
for ri, row in enumerate(rows14):
    tbl.rows[ri].height = E(46)
    for ci, val in enumerate(row):
        c = tbl.cell(ri, ci)
        c.margin_left = E(10); c.margin_right = E(10)
        c.margin_top = E(2); c.margin_bottom = E(2)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor.from_string(BLUE if ri == 0 else (WHITE if ri % 2 else BG2))
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if ci < 3 else PP_ALIGN.LEFT
        r = p.add_run()
        _set_run(r, val, 14 if ri else 15, WHITE if ri == 0 else TXT, ri == 0 or ci == 0)
rich_strip(s, 40, 584, 1200, 62,
           [[("结论：", {"bold": True}),
             ("YOLO11 以更少参数达到同等精度，更适合边缘设备部署；追求极致推理速度时可选 YOLOv8。数据来源：runs/comparison/comparison_metrics.csv。", {})]],
           size=16)

# ============ 15 头围精度 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 3 章 · 实验与结果分析", "15 / 19")
title_row(s, "头围估计精度：MAD / DSC / 相关性", "以检测框拟合椭圆换算毫米后对比官方真值")
IMG(s, A + "comparison_plots.png", 40, 156, 590, 426)
R(s, 40, 156, 590, 426, fill=None, line=LINE, lw=1)
T(s, 40, 590, 620, 22, "compare.py 输出的四联对比图（检测精度 / 头围误差 / Dice / 相关性）",
  size=12, color=GRAY)
kpi15 = [
    ("2.03", "MAD（YOLOv8）vs 2.39（YOLO11）", "相对平均头围 174 mm，误差约 1.2–1.4%，头围估计相当可靠。"),
    ("0.97", "DSC ≈ 0.970（两模型一致）", "预测椭圆与真实椭圆区域高度重叠，形状还原质量好。"),
    ("0.999", "Pearson r ≈ 0.999", "预测与真值接近完全线性，无系统性高估或低估。"),
]
ky = 156
for num, t1, b1 in kpi15:
    R(s, 684, ky, 556, 138, fill=LIGHT2, line=LINE, lw=1, round_=0.1)
    T(s, 704, ky, 160, 138, num, size=40, color=BLUE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 864, ky + 22, 360, 30, t1, size=15, color=DEEP, bold=True)
    T(s, 864, ky + 58, 360, 66, b1, size=13, color=SUB, leading=1.3)
    ky += 152
rich_strip(s, 40, 620, 1200, 36,
           [[("教学要点：", {"bold": True}),
             ("检测框好，头围才准——框的边界误差会通过椭圆周长直接传递到毫米级测量结果。", {})]],
           size=15)

# ============ 16 结果可视化 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 3 章 · 实验与结果分析", "16 / 19")
title_row(s, "检测结果可视化：模型看到了什么", "YOLO11n · 验证集预测（val_batch0_pred）")
IMG(s, A + "val_pred_yolo11.jpg", 40, 156, 700, 472)
R(s, 40, 156, 700, 472, fill=None, line=LINE, lw=1)
T(s, 40, 634, 710, 22, "验证集 16 张预测：蓝色框为 fetal_head 检测结果，右上角为置信度",
  size=12, color=GRAY)
ins16 = [("① 全检出", "该批次全部图像检出胎头（Recall = 1.0），置信度普遍 0.7–1.0。"),
         ("② 困难样本也稳", "小孕周小胎头、混响伪影、体位偏斜等困难样本仍被稳定框选。"),
         ("③ 框即测量入口", "框贴合颅骨椭圆轮廓，可直接进入“拟合椭圆 → 换算毫米”环节。")]
iy = 156
for t1, b1 in ins16:
    card(s, 774, iy, 466, 148, t1, b1, tsize=19, bsize=15)
    iy += 162
R(s, 40, 662, 1200, 44, fill=DEEP, round_=0.12)
T(s, 40, 662, 1200, 44, "预测框 → 拟合椭圆 → 周长 × 像素尺寸 → 头围（mm）",
  size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
pageno_only(s, "16 / 19", white=True)

# ============ 22 章节扉页04 课堂任务 ============
section_slide("04", "PART 04", "课堂任务 · 动手实践",
              ["任务：用 best.pt 对官方测试集完成一次头围自动测量",
               "三个环节：批量推理 → 几何换算 → 合理性检查",
               "配套脚本 scripts/class_task.py，可直接运行复现"],
              A + "task_vis_samples.png", "任务输出示例：检测框 + 拟合椭圆 + 头围标注")

# ============ 23 课堂任务书 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 4 章 · 课堂任务")
title_row(s, "课堂任务书：头围自动测量挑战", "建议用时 30 分钟 · 1–2 人一组")
R(s, 40, 156, 560, 238, fill=DEEP, round_=0.08)
T(s, 66, 172, 510, 30, "任务背景", size=21, color=WHITE, bold=True)
T(s, 66, 206, 510, 92,
  "你是算法实习生。临床同事交给你 335 张无标注的官方测试集超声图，要求用训练好的 YOLO11n 模型自动测出每张图的胎儿头围（mm），并核对结果是否合理。",
  size=14.5, color=WHITE, leading=1.4)
T(s, 66, 300, 510, 84,
  [[("任务输入", {"bold": True})],
   [("best.pt · data/test_set/ · test_set_pixel_size.csv", {"font": "Consolas", "size": 12.5})],
   [("输出：每张图的头围 hc_mm（毫米）", {"size": 12.5, "color": "C7D8F5"})]],
  size=14, color=WHITE, leading=1.25)
steps23 = [
    ("① 运行脚本", [("python scripts/class_task.py --model <best.pt> --num 20", {"font": "Consolas", "size": 11}),
                    ("--out runs/class_task ｜ --num 0 表示全部 335 张", {"size": 11})]),
    ("② 逐图结果", [("打开 runs/class_task/task_predictions.csv：每张图的置信度、椭圆半轴与 hc_mm。", {})]),
    ("③ 合理性检查", [("查看 hc_distribution.png 头围分布与 vis_samples.png 可视化样张，人工核对框和数值。", {})]),
    ("④ 完成分析", [("写 200 字分析：头围范围是否覆盖小孕周到足月？哪类图像最可能出错？", {})]),
]
sy = 156
for idx, (t1, b1) in enumerate(steps23, 1):
    R(s, 624, sy, 616, 90, fill=LIGHT2, line=LINE, lw=1, round_=0.1)
    R(s, 644, sy + 27, 36, 36, fill=BLUE, round_=0.25)
    T(s, 644, sy + 27, 36, 36, str(idx), size=15, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 696, sy + 12, 530, 26, t1[2:], size=17, color=DEEP, bold=True)
    T(s, 696, sy + 40, 530, 46, b1, size=11.5, color=SUB, leading=1.25)
    sy += 100
rich_strip(s, 40, 408, 560, 56,
           [[("交付物：", {"bold": True}),
             ("task_predictions.csv + 200 字分析 + 1 个易错样例截图。", {})]],
           size=14)
R(s, 40, 478, 560, 178, fill=LIGHT, line=LINE, lw=1, round_=0.08)
T(s, 64, 490, 512, 26, "进阶挑战（三选一）", size=18, color=DEEP, bold=True)
T(s, 64, 522, 512, 126,
  ["A. --num 0 跑全部 335 张，找出置信度最低的 5 张图。",
   "B. 分别用 YOLOv8n 与 YOLO11n 各跑一遍，找头围差 > 5 mm 的图并分析原因。",
   "C. 验证“正圆假设”是否在斜位胎头上高估头围？（提示：按 ground truth 的 angle 分组对比）"],
  size=12, color=SUB, leading=1.45)

# ============ 24 任务参考输出 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 4 章 · 课堂任务")
title_row(s, "任务参考输出与课堂讨论", "class_task.py 实际运行结果（--num 12）")
IMG(s, A + "task_vis_samples.png", 40, 156, 640, 373)
R(s, 40, 156, 640, 373, fill=None, line=LINE, lw=1)
T(s, 40, 534, 640, 22, "可视化样张：红框 = YOLO 检测框，蓝椭圆 = 由框拟合的椭圆，左上角为头围与置信度",
  size=12, color=GRAY)
R(s, 40, 566, 640, 100, fill=LIGHT, round_=0.1)
T(s, 64, 578, 592, 26, "讨论：误差可能来自哪里？", size=18, color=DEEP, bold=True)
T(s, 64, 608, 592, 50,
  "注意第 1、5 张：胎头呈斜椭圆，而检测框是正圆——用“框宽高的一半”当椭圆半轴会带来系统误差。",
  size=14, color=SUB, leading=1.4)
stats24 = [("12 / 12", "全部检出，未出现漏检"), ("74.7 – 343.6 mm", "头围跨度大，覆盖小孕周到足月"),
           ("0.794", "最低置信度（仍 > 0.75）")]
ty = 156
for num, lab in stats24:
    R(s, 700, ty, 540, 64, fill=LIGHT2, line=LINE, lw=1, round_=0.12)
    T(s, 724, ty, 230, 64, num, size=24, color=BLUE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 956, ty, 264, 64, lab, size=14, color=SUB, anchor=MSO_ANCHOR.MIDDLE)
    ty += 74
IMG(s, A + "task_hc_distribution.png", 745, 390, 450, 270)
R(s, 745, 390, 450, 270, fill=None, line=LINE, lw=1)

# ============ 25 章节扉页05 ============
section_slide("05", "PART 05", "总结与展望",
              ["三条结论：流程可行 · 精度相当 · 架构各有取舍",
               "三个方向：椭圆回归 · 分割联合 · 临床化评估"],
              A + "val_pred_yolov8.jpg", "YOLOv8n 验证集预测：与 YOLO11 表现同样可靠")

# ============ 26 结论与展望 ============
s = prs.slides.add_slide(BLANK)
header(s, "第 5 章 · 总结与展望", "26 / 27")
title_row(s, "结论与展望")
R(s, 40, 156, 660, 416, fill=DEEP, round_=0.08)
T(s, 66, 176, 300, 40, "三条结论", size=24, color=WHITE, bold=True)
concl = [
    "“掩膜 → 椭圆 → YOLO 框”的标注转换流程端到端可行，单类检测 mAP50 达到 0.995。",
    "两代模型检测精度几乎持平（mAP50-95：0.955 vs 0.952）；头围误差 YOLOv8 略小（MAD 2.03 vs 2.39 mm），DSC 均 ≈ 0.97。",
    "YOLO11 参数少约 17%、权重小 1 MB，同等精度下更适合资源受限的部署场景。",
]
cy = 232
for i, c1 in enumerate(concl, 1):
    R(s, 66, cy, 34, 34, fill=WHITE, alpha=0.18, round_=0.5)
    T(s, 66, cy, 34, 34, str(i), size=15, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    T(s, 114, cy - 4, 560, 100, c1, size=15, color=WHITE, leading=1.4)
    cy += 112
T(s, 724, 160, 400, 36, "三个改进方向", size=24, color=DEEP, bold=True)
future = [("① 直接回归椭圆参数", "让模型直接预测中心 / 半轴 / 角度，省去“框 → 椭圆拟合”环节，减少误差传递。"),
          ("② 检测 + 分割联合", "引入分割分支联合优化颅骨轮廓，有望压缩 mAP50-95 与 MAD 的剩余差距。"),
          ("③ 临床化评估", "按孕周分组评估误差（如 Bland–Altman、95% 一致性界限），向临床可用性靠拢。")]
fy = 208
for t1, b1 in future:
    card(s, 724, fy, 516, 118, t1, b1, tsize=18, bsize=14)
    fy += 126
rich_strip(s, 40, 592, 1200, 54,
           [[("一句话总结：", {"bold": True}),
             ("头围自动估计 = 目标检测 + 几何换算，检测与测量两条指标链都要盯住。", {})]],
           size=18)

# ============ 19 感谢页 ============
s = prs.slides.add_slide(BLANK)
R(s, 0, 0, 1280, 720, fill=DEEP)
R(s, 0, 0, 1280, 10, fill=MID)
T(s, 0, 210, 1280, 100, "谢 谢 聆 听", size=64, color=WHITE, bold=True,
  align=PP_ALIGN.CENTER)
T(s, 0, 322, 1280, 36, "Q & A · 欢迎讨论", size=22, color=WHITE,
  align=PP_ALIGN.CENTER)
R(s, 585, 380, 110, 5, fill=MID, round_=0.5)
T(s, 0, 414, 1280, 80, ["数据来源：HC18 挑战赛（ISBI 2018，Zenodo: records/1327317）",
                        "框架：Ultralytics YOLOv8 / YOLO11 · 汇报人：肖雄涛 · 2026 年 10 月"],
  size=16, color=WHITE, align=PP_ALIGN.CENTER, leading=1.7)
T(s, 0, 660, 1280, 22, "超声胎儿头围检测 · 教学课件 · 仅用于教学与科研",
  size=12, color=WHITE, align=PP_ALIGN.CENTER)

try:
    prs.save("超声胎儿头围检测.pptx")
    print(f"OK: {len(prs.slides)} slides saved -> 超声胎儿头围检测.pptx")
except PermissionError:
    prs.save("超声胎儿头围检测_完整版27页.pptx")
    print(f"OK: {len(prs.slides)} slides saved -> 超声胎儿头围检测_完整版27页.pptx（原文件被预览占用）")
