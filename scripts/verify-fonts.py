#!/usr/bin/env python3
"""
verify-fonts.py - 验证合并后的字体，检查关键 Unicode 范围覆盖
"""

import argparse
import os
import sys

import toml
from fontTools.ttLib import TTFont


def load_unicode_ranges(config_path):
    """加载 Unicode 范围配置"""
    with open(config_path, "r") as f:
        config = toml.load(f)

    ranges = {}
    for name, data in config.items():
        if isinstance(data, dict) and "range" in data:
            ranges[name] = {
                "range": tuple(data["range"]),
                "description": data.get("description", name),
                "priority": data.get("priority", 2),
            }
    return ranges


def verify_font(font_path, ranges_config):
    """验证单个字体文件"""
    print(f"\n{'=' * 70}")
    print(f"Verifying: {font_path}")
    print(f"{'=' * 70}")

    # 加载 Unicode 范围配置
    unicode_ranges = load_unicode_ranges(ranges_config)

    try:
        font = TTFont(font_path)
    except Exception as e:
        print(f"  ERROR: Cannot load font: {e}")
        return False

    # 检查必要的表
    required_tables = [
        "cmap",
        "glyf",
        "head",
        "hhea",
        "hmtx",
        "loca",
        "maxp",
        "name",
        "post",
    ]
    missing_tables = [t for t in required_tables if t not in font]

    if missing_tables:
        print(f"  WARNING: Missing tables: {', '.join(missing_tables)}")
    else:
        print(f"  ✓ All required tables present")

    # 检查 cmap
    cmap = font.getBestCmap()
    if not cmap:
        print(f"  ERROR: No cmap found")
        return False

    print(f"  ✓ cmap entries: {len(cmap)}")

    # 验证每个 Unicode 范围
    print(f"\n  {'=' * 60}")
    print(f"  Unicode Range Coverage")
    print(f"  {'=' * 60}")

    total_glyphs = 0
    missing_important = []

    # 按优先级排序
    sorted_ranges = sorted(unicode_ranges.items(), key=lambda x: x[1]["priority"])

    for range_name, range_data in sorted_ranges:
        start, end = range_data["range"]
        description = range_data["description"]
        priority = range_data["priority"]

        # 计算该范围内的字形数量
        count = sum(1 for k in cmap if start <= k <= end)
        total_glyphs += count

        # 状态符号
        if priority == 0:
            status = "★"  # 最高优先级
        elif priority == 1:
            status = "●"  # 核心
        elif priority == 2:
            status = "○"  # 扩展
        else:
            status = "·"  # 罕见

        # 颜色和标记
        if count == 0:
            missing_important.append((range_name, description))
            marker = "△ EMPTY"
        else:
            marker = "✓"

        print(f"  {status} {description:40s} {count:6d} glyphs  {marker}")

    print(f"  {'=' * 60}")
    print(f"  Total glyphs: {total_glyphs}")

    # 显示缺失的范围
    if missing_important:
        print(f"\n  ⚠ EMPTY RANGES:")
        for name, desc in missing_important:
            print(f"    - {desc}")

    # 检查文件大小
    file_size = os.path.getsize(font_path)
    print(f"\n  File size: {file_size / 1024 / 1024:.2f} MB")

    # 检查字体名称
    if "name" in font:
        for record in font["name"].names:
            if record.nameID == 4:  # Full name
                try:
                    name = record.toUnicode()
                    print(f"  Font name: {name}")
                    break
                except:
                    pass

    # 结论
    print(f"\n  {'=' * 60}")
    if missing_important:
        print(f"  ⚠ WARNING: {len(missing_important)} empty ranges")
        return True
    else:
        print(f"  ✓ PASSED: All ranges covered")
        return True


def main():
    parser = argparse.ArgumentParser(description="Verify merged fonts")
    parser.add_argument("directory", help="Directory containing font files to verify")
    parser.add_argument(
        "--ranges",
        default="scripts/unicode-ranges.toml",
        help="Unicode ranges config file (default: scripts/unicode-ranges.toml)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    # 检查配置文件
    if not os.path.exists(args.ranges):
        print(f"Error: Unicode ranges config not found: {args.ranges}", file=sys.stderr)
        sys.exit(1)

    # 查找所有字体文件
    font_files = []
    for f in os.listdir(args.directory):
        if f.endswith((".ttf", ".otf", ".ttc", ".otc")):
            font_files.append(os.path.join(args.directory, f))

    if not font_files:
        print(f"Error: No font files found in {args.directory}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("Font Verification")
    print("=" * 70)

    all_passed = True
    for font_path in sorted(font_files):
        if not verify_font(font_path, args.ranges):
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("All fonts verified successfully!")
    else:
        print("Some fonts failed verification!")
        sys.exit(1)


if __name__ == "__main__":
    main()
