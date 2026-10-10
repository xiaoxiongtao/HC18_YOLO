#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""matplotlib 中文字体设置工具。

按字体文件路径直接注册系统字体，比只写字体名更可靠，避免中文显示为方框（tofu）。
"""

import os

from matplotlib import font_manager


def setup_chinese_font():
    """注册一个可用的中文字体并返回其名称；找不到则返回 None。

    优先使用 Windows 常见中文字体（微软雅黑 / 黑体 / 宋体），
    再回退到 Linux / macOS 常见中文字体。
    """
    candidates = []
    win_dir = os.environ.get("WINDIR", r"C:\Windows")
    candidates += [
        os.path.join(win_dir, "Fonts", "msyh.ttc"),    # 微软雅黑
        os.path.join(win_dir, "Fonts", "simhei.ttf"),  # 黑体
        os.path.join(win_dir, "Fonts", "simsun.ttc"),  # 宋体
    ]

    # Linux / macOS 常见中文字体（按名称查找字体文件）
    for name in ("Noto Sans CJK SC", "WenQuanYi Zen Hei", "PingFang SC",
                 "Heiti SC", "Arial Unicode MS"):
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
            candidates.append(path)
        except Exception:
            pass

    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        try:
            font_manager.fontManager.addfont(path)
            return font_manager.FontProperties(fname=path).get_name()
        except Exception:
            continue
    return None
