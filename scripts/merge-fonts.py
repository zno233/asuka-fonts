#!/usr/bin/env python3
"""
merge-fonts.py - 合并多个字体源为一个字体

字体源：
1. Iosevka（通过构建生成）- 英文字形
2. Nerd Fonts - 图标字形（0xE000-0xF8FF）
3. Noto Sans CJK SC - 中文字符（等宽）
4. Noto Sans CJK JP - 日文字符（等宽）

输出：HanekokoroNerdCJK-Regular.ttf
"""

import argparse
import os
import sys
import toml
from fontTools.ttLib import TTFont, TTCollection
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
import copy

def load_unicode_ranges(config_path):
    """加载 Unicode 范围配置"""
    with open(config_path, 'r') as f:
        config = toml.load(f)

    ranges = {}
    for name, data in config.items():
        if isinstance(data, dict) and 'range' in data:
            ranges[name] = {
                'range': tuple(data['range']),
                'description': data.get('description', name),
                'priority': data.get('priority', 2)
            }
    return ranges

def load_font(path):
    """加载字体文件"""
    print(f"  Loading: {path}")
    if path.endswith('.ttc') or path.endswith('.otc'):
        collection = TTCollection(path)
        return collection[0]
    return TTFont(path)

def get_cmap(font):
    """获取字体的 cmap 表"""
    return font.getBestCmap() or {}

def extract_glyphs_by_range(font, start, end):
    """提取指定 Unicode 范围的字形"""
    cmap = get_cmap(font)
    glyphs = {}
    for unicode_val, glyph_name in cmap.items():
        if start <= unicode_val <= end:
            glyphs[unicode_val] = glyph_name
    return glyphs

def copy_glyph(src_font, dst_font, glyph_name):
    """复制单个字形

    支持两种源字体：
    - TrueType（glyf）：直接复制字形
    - CFF（如 Noto Sans CJK 的 .otf）：把三次贝塞尔轮廓转换为 TrueType 二次轮廓
    """
    if 'glyf' in src_font:
        # TrueType 源
        if glyph_name not in src_font['glyf'].glyphs:
            return False
        glyph = src_font['glyf'].glyphs[glyph_name]
        dst_font['glyf'].glyphs[glyph_name] = glyph
        _add_glyph_order(dst_font, glyph_name)
        _add_glyph_metrics(src_font, dst_font, glyph_name)
        return True
    elif 'CFF ' in src_font:
        # CFF 源：通过 Cu2QuPen 将三次曲线转成二次曲线后写入目标 glyf
        glyph_set = src_font.getGlyphSet()
        if glyph_name not in glyph_set:
            return False
        tt_pen = TTGlyphPen(dst_font.getGlyphSet())
        cu2qu_pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True)
        glyph_set[glyph_name].draw(cu2qu_pen)
        dst_font['glyf'].glyphs[glyph_name] = tt_pen.glyph()
        _add_glyph_order(dst_font, glyph_name)
        _add_glyph_metrics(src_font, dst_font, glyph_name)
        return True
    return False


def _add_glyph_order(font, glyph_name):
    """向字体 glyphOrder 追加新字形名，保持 glyf.glyphOrder 与 glyphs 一致"""
    if glyph_name not in font.getGlyphOrder():
        font.setGlyphOrder(font.getGlyphOrder() + [glyph_name])


def _add_glyph_metrics(src_font, dst_font, glyph_name):
    """复制字形宽度度量到目标字体 hmtx，避免保存时 maxp 重算 KeyError"""
    if 'hmtx' not in src_font or 'hmtx' not in dst_font:
        return
    src_metrics = src_font['hmtx'].metrics
    dst_metrics = dst_font['hmtx'].metrics
    if glyph_name in dst_metrics:
        return
    if glyph_name in src_metrics:
        dst_metrics[glyph_name] = src_metrics[glyph_name]
    else:
        # 兜底：沿用目标字体现有字形的默认度量
        default = next(iter(dst_metrics.values()), (600, 0))
        dst_metrics[glyph_name] = default

def merge_fonts(base_path, cjk_sc_path, cjk_jp_path, output_dir, ranges_config):
    """合并字体"""

    print("=" * 60)
    print("Font Merge Tool")
    print("=" * 60)

    # 加载 Unicode 范围配置
    unicode_ranges = load_unicode_ranges(ranges_config)

    # 加载源字体
    print("\n[1/6] Loading source fonts...")
    base_font = load_font(base_path)
    cjk_sc_font = load_font(cjk_sc_path)
    cjk_jp_font = load_font(cjk_jp_path)

    # 提取字形
    print("\n[2/6] Extracting glyphs...")

    # 基础字体（英文+图标）
    base_cmap = get_cmap(base_font)
    print(f"  Base font glyphs: {len(base_cmap)}")

    # 提取所有需要的字符范围
    all_glyphs = {}

    # 按优先级排序
    sorted_ranges = sorted(unicode_ranges.items(), key=lambda x: x[1]['priority'])

    for range_name, range_data in sorted_ranges:
        start, end = range_data['range']
        description = range_data['description']

        # 跳过已经在基础字体中的范围
        if range_name in ['private_use_area']:
            print(f"  Skipping {range_name} (icons already in base font)")
            continue

        # 根据字符类型选择源字体
        if range_name.startswith('cjk_') or range_name in ['hangul_syllables', 'hangul_jamo', 'hangul_jamo_extended_a', 'hangul_jamo_extended_b']:
            # CJK 字符使用 SC 字体
            glyphs = extract_glyphs_by_range(cjk_sc_font, start, end)
            print(f"  {description}: {len(glyphs)} glyphs (from CJK SC)")
        elif range_name in ['hiragana', 'katakana', 'katakana_phonetic_extensions']:
            # 日文假名使用 JP 字体
            glyphs = extract_glyphs_by_range(cjk_jp_font, start, end)
            print(f"  {description}: {len(glyphs)} glyphs (from CJK JP)")
        else:
            # 其他字符使用基础字体
            glyphs = extract_glyphs_by_range(base_font, start, end)
            print(f"  {description}: {len(glyphs)} glyphs (from base)")

        # 合并字形（不覆盖已存在的）
        for unicode_val, glyph_name in glyphs.items():
            if unicode_val not in all_glyphs:
                all_glyphs[unicode_val] = (glyph_name, range_name)

    print(f"\n  Total unique glyphs: {len(all_glyphs)}")

    # 合并字形到输出字体
    print("\n[3/6] Merging glyphs...")

    # 使用 base_font 作为基础
    output_font = copy.deepcopy(base_font)

    # 添加 CJK 字符
    added_cjk = 0
    for unicode_val, (glyph_name, range_name) in all_glyphs.items():
        if range_name.startswith('cjk_') or range_name in ['hangul_syllables', 'hangul_jamo', 'hangul_jamo_extended_a', 'hangul_jamo_extended_b']:
            if glyph_name not in output_font['glyf'].glyphs:
                if copy_glyph(cjk_sc_font, output_font, glyph_name):
                    added_cjk += 1

    # 添加日文假名
    added_jp = 0
    for unicode_val, (glyph_name, range_name) in all_glyphs.items():
        if range_name in ['hiragana', 'katakana', 'katakana_phonetic_extensions']:
            if glyph_name not in output_font['glyf'].glyphs:
                if copy_glyph(cjk_jp_font, output_font, glyph_name):
                    added_jp += 1

    # 添加其他字符
    added_other = 0
    for unicode_val, (glyph_name, range_name) in all_glyphs.items():
        if not range_name.startswith('cjk_') and range_name not in ['hangul_syllables', 'hangul_jamo', 'hangul_jamo_extended_a', 'hangul_jamo_extended_b', 'hiragana', 'katakana', 'katakana_phonetic_extensions']:
            if glyph_name not in output_font['glyf'].glyphs:
                if copy_glyph(base_font, output_font, glyph_name):
                    added_other += 1

    print(f"  Added {added_cjk} CJK glyphs")
    print(f"  Added {added_jp} Japanese kana glyphs")
    print(f"  Added {added_other} other glyphs")

    # 更新 cmap 表
    print("\n[4/6] Updating cmap table...")
    cmap = output_font.getBestCmap()

    # 添加所有字符
    for unicode_val, (glyph_name, range_name) in all_glyphs.items():
        cmap[unicode_val] = glyph_name

    print(f"  Total glyphs in cmap: {len(cmap)}")

    # 验证字符覆盖
    print("\n[5/6] Verifying coverage...")

    # 检查关键范围
    critical_ranges = [
        ('ASCII', 0x0000, 0x007F),
        ('Latin Extended', 0x0080, 0x024F),
        ('Greek', 0x0370, 0x03FF),
        ('Cyrillic', 0x0400, 0x04FF),
        ('Arabic', 0x0600, 0x06FF),
        ('CJK Unified', 0x4E00, 0x9FFF),
        ('Hiragana', 0x3040, 0x309F),
        ('Katakana', 0x30A0, 0x30FF),
        ('Hangul', 0xAC00, 0xD7AF),
        ('Private Use (Icons)', 0xE000, 0xF8FF),
    ]

    for name, start, end in critical_ranges:
        count = sum(1 for k in cmap if start <= k <= end)
        print(f"  {name}: {count} glyphs")

    # 保存
    print("\n[6/6] Saving output...")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(base_path))
    output_font.save(output_path)

    file_size = os.path.getsize(output_path)
    print(f"\n{'=' * 60}")
    print(f"Output: {output_path}")
    print(f"Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"{'=' * 60}")

    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple fonts into one (Base + CJK)"
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base font path (English glyphs + Icons, e.g., Iosevka Nerd)"
    )
    parser.add_argument(
        "--cjk-sc",
        required=True,
        help="CJK SC font path (Noto Sans CJK SC)"
    )
    parser.add_argument(
        "--cjk-jp",
        required=True,
        help="CJK JP font path (Noto Sans CJK JP)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory"
    )
    parser.add_argument(
        "--ranges",
        default="scripts/unicode-ranges.toml",
        help="Unicode ranges config file (default: scripts/unicode-ranges.toml)"
    )

    args = parser.parse_args()

    # 检查文件是否存在
    for path, name in [
        (args.base, "Base font"),
        (args.cjk_sc, "CJK SC font"),
        (args.cjk_jp, "CJK JP font"),
        (args.ranges, "Unicode ranges config"),
    ]:
        if not os.path.exists(path):
            print(f"Error: {name} not found: {path}", file=sys.stderr)
            sys.exit(1)

    merge_fonts(args.base, args.cjk_sc, args.cjk_jp, args.output, args.ranges)

if __name__ == "__main__":
    main()
