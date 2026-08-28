#!/usr/bin/env python3
"""从 zip 中提取匹配条目（按文件名或后缀），供 CI 下载步骤复用。

用法示例：
  python3 scripts/extract-zip.py a.zip out/ --name file1.ttf --name file2.ttf --required
  python3 scripts/extract-zip.py a.zip out/ --suffix .otf
"""

import argparse
import os
import sys
import zipfile


def main():
    parser = argparse.ArgumentParser(description="Extract matching entries from a zip archive")
    parser.add_argument("zip", help="Path to the zip archive")
    parser.add_argument("outdir", help="Output directory")
    parser.add_argument(
        "--name",
        action="append",
        default=[],
        help="Extract entries whose basename equals this name (repeatable)",
    )
    parser.add_argument(
        "--suffix",
        action="append",
        default=[],
        help="Extract entries whose basename ends with this suffix (repeatable)",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Exit with error if no matching entry is found",
    )
    args = parser.parse_args()

    if not args.name and not args.suffix:
        parser.error("at least one of --name / --suffix is required")

    with zipfile.ZipFile(args.zip) as zf:
        matched = []
        for entry in zf.namelist():
            base = os.path.basename(entry)
            if any(base == n for n in args.name) or any(base.endswith(s) for s in args.suffix):
                matched.append(entry)

        if not matched and args.required:
            print(
                f"Error: no entries matching names={args.name} suffix={args.suffix} in {args.zip}",
                file=sys.stderr,
            )
            sys.exit(1)

        os.makedirs(args.outdir, exist_ok=True)
        for entry in matched:
            zf.extract(entry, args.outdir)
            print(f"Extracted: {entry}")


if __name__ == "__main__":
    main()
