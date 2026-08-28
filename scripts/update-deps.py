#!/usr/bin/env python3
"""
update-deps.py - 检查并更新依赖版本
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

import toml


def load_dependencies(config_path):
    """加载依赖配置"""
    with open(config_path, "r") as f:
        return toml.load(f)


def save_dependencies(config_path, config):
    """保存依赖配置"""
    with open(config_path, "w") as f:
        toml.dump(config, f)


def get_github_latest_release(repo):
    """获取 GitHub 仓库的最新 release 版本"""
    try:
        # 使用 gh CLI
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/releases/latest", "--jq", ".tag_name"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip().lstrip("v")
    except FileNotFoundError:
        pass

    # 备用：使用 API
    try:
        import urllib.request

        url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "AsukaFonts"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data["tag_name"].lstrip("v")
    except Exception as e:
        print(f"  Warning: Cannot fetch latest version for {repo}: {e}")
        return None


def get_github_default_branch(repo):
    """获取 GitHub 仓库的默认分支"""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return "main"


def check_updates(config, check_all=False):
    """检查依赖更新"""
    print("=" * 60)
    print("Checking for dependency updates...")
    print("=" * 60)

    updates = []

    # Iosevka
    print(f"\n[iosevka] ({config['iosevka']['repo']})")
    if config["iosevka"].get("tag"):
        # 锁定 tag 模式：对比最新 release tag
        latest = get_github_latest_release(config["iosevka"]["repo"])
        current = config["iosevka"]["tag"]
        print(f"  Current: {current}")
        print(f"  Latest:  {latest}")
        if latest and current.lstrip("v") != latest:
            updates.append(("iosevka", "tag", f"v{latest}"))
            print(f"  → Update available!")
        else:
            print(f"  ✓ Up to date")
    else:
        # 分支模式：对比默认分支
        latest = get_github_default_branch(config["iosevka"]["repo"])
        current = config["iosevka"].get("branch", "master")
        print(f"  Current: {current}")
        print(f"  Latest:  {latest}")
        if current != latest:
            updates.append(("iosevka", "branch", latest))
            print(f"  → Update available!")
        else:
            print(f"  ✓ Up to date")

    # Nerd Fonts
    print(f"\n[nerd-fonts] ({config['nerd-fonts']['repo']})")
    latest = get_github_latest_release(config["nerd-fonts"]["repo"])
    current = config["nerd-fonts"].get("version", "unknown")
    print(f"  Current: v{current}")
    print(f"  Latest:  v{latest}" if latest else "  Latest:  unknown")
    if latest and current != latest:
        updates.append(("nerd-fonts", "version", latest))
        print(f"  → Update available!")
    else:
        print(f"  ✓ Up to date")

    # Noto CJK
    print(f"\n[noto-cjk] ({config['noto-cjk']['repo']})")
    latest = get_github_latest_release(config["noto-cjk"]["repo"])
    current = config["noto-cjk"].get("version", "unknown")
    print(f"  Current: {current}")
    print(f"  Latest:  {latest}" if latest else "  Latest:  unknown")
    if latest and current != latest:
        updates.append(("noto-cjk", "version", latest))
        print(f"  → Update available!")
    else:
        print(f"  ✓ Up to date")

    return updates


def apply_updates(config, updates):
    """应用更新"""
    for dep, field, value in updates:
        if field == "version":
            config[dep]["version"] = value
        elif field == "branch":
            config[dep]["branch"] = value
        print(f"Updated {dep}.{field} = {value}")
    return config


def generate_update_workflow(config):
    """生成更新 workflow"""
    return f"""name: Check Dependency Updates

on:
  schedule:
    # 每周一 UTC 0:00 检查更新
    - cron: '0 0 * * 1'
  workflow_dispatch:

jobs:
  check-updates:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install toml

      - name: Check for updates
        id: check
        run: |
          python3 scripts/update-deps.py check > output.txt 2>&1 || true
          cat output.txt

          # 检查是否有更新
          if grep -q "→ Update available" output.txt; then
            echo "has_updates=true" >> $GITHUB_OUTPUT
          else
            echo "has_updates=false" >> $GITHUB_OUTPUT
          fi

      - name: Create Pull Request
        if: steps.check.outputs.has_updates == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{{{ secrets.GITHUB_TOKEN }}}}
          commit-message: "chore: update dependencies"
          title: "chore: update dependencies"
          body: |
            Automated dependency update check.

            ```
            {chr(10).join(f"- {dep}: updated {field}" for dep, field, _ in updates) if updates else "No updates"}
            ```
          branch: chore/update-deps
          labels: dependencies
"""


def main():
    parser = argparse.ArgumentParser(description="Manage Asuka Fonts dependencies")
    parser.add_argument(
        "action",
        choices=["check", "update", "generate-workflow"],
        help="Action to perform",
    )
    parser.add_argument(
        "--config", default="dependencies.toml", help="Dependencies config file"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply updates (for 'update' action)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    config = load_dependencies(args.config)

    if args.action == "check":
        updates = check_updates(config)
        if updates:
            print(f"\n{'=' * 60}")
            print(f"Found {len(updates)} updates available")
            print(f"Run 'python3 scripts/update-deps.py update --apply' to apply")
        else:
            print(f"\n{'=' * 60}")
            print("All dependencies are up to date!")

    elif args.action == "update":
        updates = check_updates(config)
        if updates:
            if args.apply:
                config = apply_updates(config, updates)
                save_dependencies(args.config, config)
                print(f"\n✓ Applied {len(updates)} updates")
            else:
                print(f"\nDry run. Use --apply to apply updates")
        else:
            print("\nNo updates to apply")

    elif args.action == "generate-workflow":
        workflow = generate_update_workflow(config)
        print(workflow)


if __name__ == "__main__":
    main()
