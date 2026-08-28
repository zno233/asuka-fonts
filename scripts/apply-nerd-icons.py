#!/usr/bin/env python3
"""
apply-nerd-icons.py - 将 Nerd Fonts 图标字形合并到 Iosevka 字体中
"""

import argparse
import os
import sys

from fontTools.ttLib import TTFont


def load_font(path):
    print(f"  Loading: {path}")
    return TTFont(path)


def get_cmap(font):
    return font.getBestCmap() or {}


def copy_glyph(src_font, dst_font, glyph_name):
    if glyph_name not in src_font["glyf"].glyphs:
        return False
    glyph = src_font["glyf"].glyphs[glyph_name]
    dst_font["glyf"].glyphs[glyph_name] = glyph
    # 保持 glyf.glyphOrder 与 glyphs 一致（否则保存时断言失败）
    if glyph_name not in dst_font.getGlyphOrder():
        dst_font.setGlyphOrder(dst_font.getGlyphOrder() + [glyph_name])
    # 复制宽度度量，避免保存时 maxp 重算 KeyError
    if "hmtx" in src_font and "hmtx" in dst_font and glyph_name not in dst_font["hmtx"].metrics:
        src_metrics = src_font["hmtx"].metrics
        if glyph_name in src_metrics:
            dst_font["hmtx"].metrics[glyph_name] = src_metrics[glyph_name]
        else:
            dst_font["hmtx"].metrics[glyph_name] = next(iter(dst_font["hmtx"].metrics.values()), (600, 0))
    return True


def apply_nerd_icons(base_path, icons_path, output_dir):
    print("=" * 60)
    print("Apply Nerd Fonts Icons")
    print("=" * 60)

    print("\n[1/4] Loading fonts...")
    base_font = load_font(base_path)
    icons_font = load_font(icons_path)

    print("\n[2/4] Extracting icon glyphs...")
    icons_cmap = get_cmap(icons_font)

    # Nerd Fonts 图标范围：0xE000-0xF8FF (Private Use Area)
    nerd_glyphs = {}
    for unicode_val, glyph_name in icons_cmap.items():
        if 0xE000 <= unicode_val <= 0xF8FF:
            nerd_glyphs[unicode_val] = glyph_name

    print(f"  Found {len(nerd_glyphs)} icon glyphs")

    print("\n[3/4] Merging icons...")
    output_font = base_font

    added = 0
    for unicode_val, glyph_name in nerd_glyphs.items():
        if glyph_name not in output_font["glyf"].glyphs:
            if copy_glyph(icons_font, output_font, glyph_name):
                added += 1

    print(f"  Added {added} icon glyphs")

    # 更新 cmap
    cmap = output_font.getBestCmap()
    for unicode_val, glyph_name in nerd_glyphs.items():
        cmap[unicode_val] = glyph_name

    print(f"  Total glyphs in cmap: {len(cmap)}")

    print("\n[4/4] Saving output...")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(base_path))
    output_font.save(output_path)

    file_size = os.path.getsize(output_path)
    print(f"\nOutput: {output_path}")
    print(f"Size: {file_size / 1024 / 1024:.2f} MB")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Apply Nerd Fonts icons to Iosevka font"
    )
    parser.add_argument("--base", required=True, help="Base Iosevka font")
    parser.add_argument("--icons", required=True, help="Nerd Fonts icon source")
    parser.add_argument("--output", required=True, help="Output directory")

    args = parser.parse_args()

    for path, name in [(args.base, "Base font"), (args.icons, "Icons font")]:
        if not os.path.exists(path):
            print(f"Error: {name} not found: {path}", file=sys.stderr)
            sys.exit(1)

    apply_nerd_icons(args.base, args.icons, args.output)


if __name__ == "__main__":
    main()
