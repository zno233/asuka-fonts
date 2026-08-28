#!/usr/bin/env python3
"""
check-coverage.py - 检查字体的字符覆盖情况
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


def check_coverage(font_path, ranges_config):
    """检查字体的字符覆盖情况"""
    print(f"\nChecking coverage for: {font_path}")
    print("=" * 70)

    # 加载 Unicode 范围配置
    unicode_ranges = load_unicode_ranges(ranges_config)

    # 加载字体
    font = TTFont(font_path)
    cmap = font.getBestCmap()

    # 统计每个范围的覆盖情况
    results = []
    for range_name, range_data in sorted(
        unicode_ranges.items(), key=lambda x: x[1]["priority"]
    ):
        start, end = range_data["range"]
        description = range_data["description"]
        priority = range_data["priority"]

        # 计算范围内的总字符数
        total_chars = end - start + 1

        # 计算字体中已有的字符数
        covered_chars = sum(1 for k in cmap if start <= k <= end)

        # 计算覆盖率
        coverage_percent = (covered_chars / total_chars * 100) if total_chars > 0 else 0

        results.append(
            {
                "name": range_name,
                "description": description,
                "priority": priority,
                "total": total_chars,
                "covered": covered_chars,
                "percent": coverage_percent,
            }
        )

    # 输出结果
    print(
        f"\n{'Description':<45} {'Total':>8} {'Covered':>8} {'Percent':>8} {'Status':>10}"
    )
    print("-" * 85)

    for r in results:
        # 状态判断
        if r["priority"] == 0:
            status = "★ REQUIRED"
        elif r["priority"] == 1:
            if r["percent"] >= 90:
                status = "✓ GOOD"
            elif r["percent"] >= 50:
                status = "△ PARTIAL"
            else:
                status = "✗ LOW"
        elif r["priority"] == 2:
            if r["percent"] >= 50:
                status = "✓ GOOD"
            elif r["percent"] >= 10:
                status = "△ PARTIAL"
            else:
                status = "○ LOW"
        else:
            status = "· OPTIONAL"

        print(
            f"{r['description']:<45} {r['total']:>8} {r['covered']:>8} {r['percent']:>7.1f}% {status:>10}"
        )

    # 总结
    print("\n" + "=" * 70)
    total_chars = sum(r["total"] for r in results)
    total_covered = sum(r["covered"] for r in results)
    overall_percent = (total_covered / total_chars * 100) if total_chars > 0 else 0

    print(f"Overall: {total_covered}/{total_chars} characters ({overall_percent:.1f}%)")

    # 检查关键范围
    critical_ranges = [
        "ascii",
        "latin_extended_a",
        "cjk_unified_ideographs",
        "hiragana",
        "katakana",
        "hangul_syllables",
        "private_use_area",
    ]

    missing_critical = []
    for r in results:
        if r["name"] in critical_ranges and r["covered"] == 0:
            missing_critical.append(r["description"])

    if missing_critical:
        print(f"\n⚠ CRITICAL MISSING: {', '.join(missing_critical)}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Check font character coverage")
    parser.add_argument("font", help="Font file to check")
    parser.add_argument(
        "--ranges",
        default="scripts/unicode-ranges.toml",
        help="Unicode ranges config file",
    )

    args = parser.parse_args()

    if not os.path.exists(args.font):
        print(f"Error: Font not found: {args.font}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.ranges):
        print(f"Error: Config not found: {args.ranges}", file=sys.stderr)
        sys.exit(1)

    success = check_coverage(args.font, args.ranges)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
