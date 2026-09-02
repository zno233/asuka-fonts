# Asuka Fonts

基于 [Iosevka](https://github.com/be5invis/Iosevka) 的字体合并项目，集成 Nerd Fonts 图标和非西文字符支持。英文字形配置参考自 [Hanekokoro Fonts](https://github.com/ShadowRZ/hanekokoro-fonts)。

## 字体来源

| 组件 | 来源 | 用途 |
|------|------|------|
| **英文字形** | [Iosevka](https://github.com/be5invis/Iosevka) + Asuka 构建配置 | 自定义字形变体 |
| **图标** | [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | 终端图标支持 |
| **Mono CJK** | [LXGW WenKai Mono](https://github.com/lxgw/LxgwWenKai) | 等宽字体的非西文字符 |
| **Sans CJK** | [文源圆体](https://github.com/takushun-wu/WenYuanFonts) | 比例字体的非西文字符（简体中文优先） |

## 特性

- ✅ 自定义 Iosevka 字形设计
- ✅ Nerd Fonts 图标支持（~9000+ 图标）
- ✅ 非西文字符支持（中日韩、希腊、西里尔等）
- ✅ 两种变体：Sans（比例）和 Mono（等宽）
- ✅ 多字重支持（Light/Regular/Bold）
- ✅ 双格式输出：TTF + OTF

## 构建配置

项目使用 Iosevka 的构建系统，配置文件：

- `private-build-plans.toml` - 自定义构建计划（Asuka 字形变体）
- `build-plans.toml` - Iosevka 基础构建配置
- `dependencies.toml` - 依赖版本集中管理

### 构建的字体变体

| 字体 | 间距 | 字重 | 非西文字体 | 用途 |
|------|------|------|----------|------|
| `AsukaMono-Light` | 等宽 | Light | LXGW WenKai Mono Light | 终端、代码 |
| `AsukaMono-Regular` | 等宽 | Regular | LXGW WenKai Mono Regular | 终端、代码 |
| `AsukaMono-Bold` | 等宽 | Bold | LXGW WenKai Mono Medium | 终端、代码 |
| `AsukaSans-Light` | 比例 | Light | 文源圆体 | 阅读、文档 |
| `AsukaSans-Regular` | 比例 | Regular | 文源圆体 | 阅读、文档 |
| `AsukaSans-Bold` | 比例 | Bold | 文源圆体 | 阅读、文档 |

## 下载

从 [Releases](https://github.com/zno233/asuka-fonts/releases) 页面下载最新版本。

## 安装

### Linux

```bash
mkdir -p ~/.local/share/fonts
cp AsukaMono-Regular.ttf AsukaSans-Regular.ttf ~/.local/share/fonts/
# 或安装 OTF 版本
cp AsukaMono-Regular.otf AsukaSans-Regular.otf ~/.local/share/fonts/
fc-cache -fv
```

### macOS

```bash
cp AsukaMono-Regular.ttf AsukaSans-Regular.ttf ~/Library/Fonts/
# 或安装 OTF 版本
cp AsukaMono-Regular.otf AsukaSans-Regular.otf ~/Library/Fonts/
```

### Windows

双击字体文件安装，或复制到 `C:\Windows\Fonts`。

## 使用

```bash
# kitty - 等宽（终端）
font_family Asuka Mono

# alacritty
[font]
family = "Asuka Mono"

# ghostty
font-family = Asuka Mono
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
LXGW_VERSION=$(python3 -c "import toml; c=toml.load('dependencies.toml'); print(c['lxgw-wenkai']['version'])")
WENYUAN_VERSION=$(python3 -c "import toml; c=toml.load('dependencies.toml'); print(c['wenyuan-rounded']['version'])")

mkdir -p sources

# Iosevka Nerd Font (Mono)
wget -O sources/IosevkaNerdFont-Regular.ttf \
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v${NF_VERSION}/IosevkaNerdFont-Regular.ttf"

# Iosevka Nerd Font Sans
wget -O sources/IosevkaNerdFontSans-Regular.ttf \
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v${NF_VERSION}/IosevkaNerdFontSans-Regular.ttf"

# LXGW WenKai Mono (for AsukaMono)
wget -O sources/LXGWWenKaiMono-Regular.ttf \
  "https://github.com/lxgw/LxgwWenKai/releases/download/v${LXGW_VERSION}/LXGWWenKaiMono-Regular.ttf"

# WenYuan Rounded SC (for AsukaSans)
wget -O sources/WenYuanRoundedSCVF.ttf \
  "https://github.com/takushun-wu/WenYuanFonts/releases/download/v${WENYUAN_VERSION}/WenYuanRoundedSCVF.ttf"

# 3. 构建 Asuka Mono
python3 scripts/merge-fonts.py \
  --base sources/IosevkaNerdFont-Regular.ttf \
  --non-latin sources/LXGWWenKaiMono-Regular.ttf \
  --output releases/

# 4. 构建 Asuka Sans
python3 scripts/merge-fonts.py \
  --base sources/IosevkaNerdFontSans-Regular.ttf \
  --non-latin sources/WenYuanRoundedSCVF.ttf \
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
- LXGW WenKai: OFL-1.1
- 文源圆体: OFL-1.1

## 致谢

- [Iosevka](https://github.com/be5invis/Iosevka)
- [Hanekokoro Fonts](https://github.com/ShadowRZ/hanekokoro-fonts) - 英文字形配置参考
- [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts)
- [LXGW WenKai](https://github.com/lxgw/LxgwWenKai) - Mono 字体的非西文字符
- [文源圆体](https://github.com/takushun-wu/WenYuanFonts) - Sans 字体的非西文字符（简体中文优先）
