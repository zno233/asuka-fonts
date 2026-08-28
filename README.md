# Asuka Fonts

基于 [Iosevka](https://github.com/be5invis/Iosevka) 的字体合并项目，集成 Nerd Fonts 图标和 CJK 字符支持。英文字形配置参考自 [Hanekokoro Fonts](https://github.com/ShadowRZ/hanekokoro-fonts)。

## 字体来源

| 组件 | 来源 | 用途 |
|------|------|------|
| **英文字形** | [Iosevka](https://github.com/be5invis/Iosevka) + Asuka 构建配置 | 自定义字形变体 |
| **图标** | [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | 终端图标支持 |
| **中文** | [Noto Sans CJK SC](https://github.com/notofonts/noto-cjk) | 简体中文 |
| **日文** | [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk) | 日文假名 |

## 特性

- ✅ Hanekokoro 自定义 Iosevka 字形设计
- ✅ Nerd Fonts 图标支持（~9000+ 图标）
- ✅ CJK 字符支持（中日韩统一汉字）
- ✅ 两种变体：Sans（比例）和 Mono（等宽）
- ✅ 多字重支持（Thin/Light/Regular/Medium/SemiBold/Bold/ExtraBold/Heavy）

## 构建配置

项目使用 Iosevka 的构建系统，配置文件：

- `private-build-plans.toml` - 自定义构建计划（Asuka 字形变体）
- `build-plans.toml` - Iosevka 基础构建配置
- `dependencies.toml` - 依赖版本集中管理

### 构建的字体变体

| 字体 | 间距 | 字重 | CJK 字体 | 用途 |
|------|------|------|----------|------|
| `AsukaMono-Light` | 等宽 | Light | Noto Sans Mono CJK Light | 终端、代码 |
| `AsukaMono-Regular` | 等宽 | Regular | Noto Sans Mono CJK | 终端、代码 |
| `AsukaMono-Bold` | 等宽 | Bold | Noto Sans Mono CJK Bold | 终端、代码 |
| `AsukaSans-Light` | 比例 | Light | Noto Sans CJK Light | 阅读、文档 |
| `AsukaSans-Regular` | 比例 | Regular | Noto Sans CJK | 阅读、文档 |
| `AsukaSans-Bold` | 比例 | Bold | Noto Sans CJK Bold | 阅读、文档 |

## 下载

从 [Releases](https://github.com/zno233/asuka-fonts/releases) 页面下载最新版本。

## 安装

### Linux

```bash
mkdir -p ~/.local/share/fonts
cp AsukaMono-Regular.ttf AsukaSans-Regular.ttf ~/.local/share/fonts/
fc-cache -fv
```

### macOS

```bash
cp AsukaMono-Regular.ttf AsukaSans-Regular.ttf ~/Library/Fonts/
```

### Windows

双击字体文件安装，或复制到 `C:\Windows\Fonts`。

## 使用

```bash
# kitty - 等宽（终端）
font_family Asuka Mono

# kitty - 比例（阅读）
font_family Asuka Sans

# alacritty
[font]
family = "Asuka Mono"

# ghostty
font-family = Asuka Mono

# waybar
font = Asuka Mono 12
```

## 依赖管理

```bash
# 检查更新
python3 scripts/update-deps.py check

# 应用更新
python3 scripts/update-deps.py update --apply
```

## 本地构建

### 前置条件

```bash
pip install fonttools brotli toml
```

### 构建步骤

```bash
# 1. 克隆项目
git clone https://github.com/zno233/asuka-fonts.git
cd asuka-fonts

# 2. 下载依赖
NF_VERSION=$(python3 -c "import toml; c=toml.load('dependencies.toml'); print(c['nerd-fonts']['version'])")
NOTO_VERSION=$(python3 -c "import toml; c=toml.load('dependencies.toml'); print(c['noto-cjk']['version'])")

mkdir -p sources

# Iosevka Nerd Font (Mono)
wget -O sources/IosevkaNerdFont-Regular.ttf \
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v${NF_VERSION}/IosevkaNerdFont-Regular.ttf"

# Iosevka Nerd Font Sans
wget -O sources/IosevkaNerdFontSans-Regular.ttf \
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v${NF_VERSION}/IosevkaNerdFontSans-Regular.ttf"

# CJK Mono
wget -O sources/NotoSansMonoCJKsc-Regular.otf \
  "https://github.com/notofonts/noto-cjk/releases/download/Sans${NOTO_VERSION}/04_NotoSansMonoCJKsc-Regular.otf"
wget -O sources/NotoSansMonoCJKjp-Regular.otf \
  "https://github.com/notofonts/noto-cjk/releases/download/Sans${NOTO_VERSION}/01_NotoSansMonoCJKjp-Regular.otf"

# CJK Sans
wget -O sources/NotoSansCJKsc-Regular.otf \
  "https://github.com/notofonts/noto-cjk/releases/download/Sans${NOTO_VERSION}/08_NotoSansCJKsc-Regular.otf"
wget -O sources/NotoSansCJKjp-Regular.otf \
  "https://github.com/notofonts/noto-cjk/releases/download/Sans${NOTO_VERSION}/04_NotoSansCJKjp-Regular.otf"

# 3. 构建 Asuka Mono
python3 scripts/merge-fonts.py \
  --base sources/IosevkaNerdFont-Regular.ttf \
  --cjk-sc sources/NotoSansMonoCJKsc-Regular.otf \
  --cjk-jp sources/NotoSansMonoCJKjp-Regular.otf \
  --output releases/

# 4. 构建 Asuka Sans
python3 scripts/merge-fonts.py \
  --base sources/IosevkaNerdFontSans-Regular.ttf \
  --cjk-sc sources/NotoSansCJKsc-Regular.otf \
  --cjk-jp sources/NotoSansCJKjp-Regular.otf \
  --output releases/

# 5. 验证
python3 scripts/verify-fonts.py releases/
```

## Unicode 范围覆盖

| 范围 | 说明 |
|------|------|
| `0x0000-0x007F` | ASCII |
| `0x0080-0x024F` | Latin Extended |
| `0x0370-0x03FF` | Greek |
| `0x0400-0x04FF` | Cyrillic |
| `0x3040-0x309F` | Hiragana |
| `0x30A0-0x30FF` | Katakana |
| `0x4E00-0x9FFF` | CJK Unified |
| `0xAC00-0xD7AF` | Hangul |
| `0xE000-0xF8FF` | Nerd Fonts Icons |

## 许可证

- Iosevka: OFL-1.1
- Nerd Fonts: MIT
- Noto Sans CJK: OFL-1.1

## 致谢

- [Iosevka](https://github.com/be5invis/Iosevka)
- [Hanekokoro Fonts](https://github.com/ShadowRZ/hanekokoro-fonts) - 英文字形配置参考
- [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts)
- [Noto Sans CJK](https://github.com/notofonts/noto-cjk)
