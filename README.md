# scan2kindle

**把只有图片的扫描版 PDF，变成 Kindle 上可调字号、可点目录的 EPUB / AZW3。**

[![Tests](https://github.com/beepony/scan2kindle/actions/workflows/test.yml/badge.svg)](https://github.com/beepony/scan2kindle/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)

[English](README.en.md) · [让 AI 安装](#让-ai-安装) · [快速开始](#快速开始) · [工作原理](docs/workflow.zh-CN.md)

```text
扫描 PDF  →  离线 OCR + 版面重建  →  EPUB 3（带目录） →  AZW3
```

## 为什么用 scan2kindle

已有工具大多解决“PDF 能搜索”或“PDF 在 Kindle 上更好看”。scan2kindle 专门解决另一个问题：**把扫描书重建成真正的电子书。**

| 工具 | 主要输出 | 和扫描书转 Kindle 电子书的差别 |
| --- | --- | --- |
| [Calibre](https://manual.calibre-ebook.com/conversion.html#convert-pdf-documents) | EPUB / AZW3 | 官方说明 PDF 是很差的转换输入，图片型、多栏 PDF 和目录支持有限 |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | 可搜索 PDF | 添加文字层，便于搜索和复制，但仍是固定版式 PDF |
| [k2pdfopt](https://www.willus.com/k2pdfopt/) | Kindle 优化 PDF | 裁剪重排页面图像，保留原貌，但不生成 EPUB 目录结构 |
| [Marker](https://github.com/datalab-to/marker) | Markdown / JSON / HTML | 擅长通用文档抽取，不专门处理 Kindle 电子书输出 |
| **scan2kindle** | **EPUB 3 + AZW3** | **OCR、版面重建、目录、插图和批量转换一次完成** |

## 特色

- **真正可重排**：按阅读顺序重建段落，在 Kindle 上可调字号、换字体。
- **目录可以点**：读取扫描目录页生成导航；能处理页码偏移、无页码目录，甚至没有目录页的书。
- **适合真实扫描件**：拆分双页扫描，识别单栏/双栏，清除页眉页码，合并跨页段落。
- **保留重要版面**：保留封面、目录页、插图和图注；复杂页面会作为图片保留。
- **离线、隐私友好**：使用 macOS Vision OCR，中文效果好，无需下载模型或 GPU，书籍不上传。
- **适合整批处理**：递归处理文件夹，可断点续跑，自动跳过重复 PDF，并生成质量报告。

实测：121 本中文扫描期刊（约 4.7 GB），平均约 0.9 秒/页；约 320 页的一本通常不到 1 分钟，生成的 EPUB 全部通过 EPUBCheck。

## 让 AI 安装

在 Codex、Claude Code 或其他能操作电脑的 AI 助手里，粘贴下面这段话。它会安装工具、创建 PDF 文件夹、等待你放入文件，然后先试转再批量转换。

> 只在本机处理文件，不会上传书籍。安装开发工具、Python 或 Calibre 时，可能需要你确认或输入电脑密码。

<details>
<summary><strong>展开并复制 AI 安装提示词</strong></summary>

````text
请帮我在这台 Mac 上安装开源工具 scan2kindle，并带我完成第一次转换。

工具地址：https://github.com/beepony/scan2kindle

它可以把扫描版 PDF 转成适合 Kindle 阅读的 EPUB 和 AZW3。

请直接执行能自动完成的步骤，用简单清楚的中文告诉我进度。只有需要我点击确认、输入密码、放入 PDF，或安装方式需要我选择时，再停下来问我。

## 基本要求

- 这个工具目前只支持 macOS。如果不是 macOS，请停止并告诉我原因。
- 不要修改、移动、删除或上传我的原始 PDF。
- 只转换我有合法使用权的书籍。
- 不要上传任何 PDF、EPUB、AZW3 或识别出来的文字。
- 不要用 sudo，除非你先说明原因并得到我的同意。
- 如果命令因为权限、沙盒或网络限制失败，请按当前 AI 工具的规则申请权限后重试，不要绕过限制。
- 不要把工具安装到 PDF 所在的文件夹里。

## 1. 检查电脑环境

1. 确认系统是 macOS。
2. 检查 git 和 swiftc 是否可用：
   - 如果不可用，运行 `xcode-select --install`。
   - 告诉我在弹出的窗口里点击“安装”。
   - 等我说安装完成后再继续。
3. 找到 Python 3.10 或更新版本：
   - 注意：macOS 自带的 python3 可能只有 3.9，不能用。
   - 如果没有合适版本，但电脑已经安装 Homebrew，可以运行 `brew install python@3.12`。
   - 如果没有 Homebrew，先向我说明有哪些安装方式，再继续。
4. 检查 Calibre 的 ebook-convert：
   - 可以在 PATH 中查找，或检查 `/Applications/calibre.app/Contents/MacOS/ebook-convert`。
   - 如果没有，但已安装 Homebrew，可以运行 `brew install --cask calibre`。
   - 如果无法安装，可以先只生成 EPUB；AZW3 需要 Calibre。

## 2. 安装 scan2kindle

1. 如果 `~/scan2kindle` 不存在，就从 GitHub 下载工具：

```zsh
git clone https://github.com/beepony/scan2kindle.git ~/scan2kindle
```

2. 如果 `~/scan2kindle` 已经存在，并且确实是这个仓库，就运行 `git pull --ff-only` 更新。如果它不是这个仓库，先问我怎么处理。
3. 创建独立的 Python 环境。把下面的 `<Python 3.10+ 路径>` 换成刚才找到的 Python：

```zsh
cd ~/scan2kindle
<Python 3.10+ 路径> -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
```

4. 安装后检查：

```zsh
.venv/bin/scan2kindle --version
.venv/bin/python -m pytest -q
```

## 3. 准备工作文件夹

创建这些文件夹：

```zsh
mkdir -p "$HOME/Kindle转换/待转换PDF"
mkdir -p "$HOME/Kindle转换/输出"
mkdir -p "$HOME/Kindle转换/试转换"
```

然后用访达打开 `$HOME/Kindle转换/待转换PDF`。

请这样告诉我：

- 把要转换的扫描 PDF 放进“待转换PDF”文件夹。
- 可以建立子文件夹，例如“2024年”“历史书”；输出时会保留同样的结构。
- 如果原 PDF 很重要，建议复制进去，原文件另外保留。
- 放好后回复“已放好”。

收到我的“已放好”后再继续。

## 4. 先试转一本

1. 找出“待转换PDF”文件夹及其子文件夹里的所有 PDF，告诉我数量和总大小。
2. 选择第一本 PDF，只转换前 30 页，结果放在“试转换”文件夹，避免影响正式结果。
3. 如果已安装 Calibre，运行：

```zsh
cd ~/scan2kindle
.venv/bin/scan2kindle "<第一本 PDF 的完整路径>" -o "$HOME/Kindle转换/试转换" --pages 1-30 --azw3 --force
```

4. 如果没有安装 Calibre，去掉 `--azw3`。
5. 第一次运行会编译 macOS 文字识别程序。如果出现 `Foundation._GenericObjCError` 或类似错误，通常是当前 AI 工具的限制导致的。请申请在当前限制之外运行后重试。
6. 试转成功后告诉我：
   - EPUB 和 AZW3 的位置；
   - 识别出多少字；
   - 生成了多少个目录项；
   - 有没有明显异常。
7. 如果电脑里有 epubcheck，也请检查试转换得到的 EPUB。

## 5. 开始批量转换

试转成功后，开始批量转换。转换时防止 Mac 休眠：

```zsh
cd ~/scan2kindle
caffeinate -dimsu .venv/bin/scan2kindle "$HOME/Kindle转换/待转换PDF" -o "$HOME/Kindle转换/输出" --azw3 2>&1 | tee -a "$HOME/Kindle转换/输出/转换日志.txt"
```

如果没有安装 Calibre，去掉 `--azw3`。

转换过程中：

- 每隔一段时间告诉我完成了几本，不要刷屏显示完整日志。
- 如果中断，请再次运行同一条命令。已经完成的书会自动跳过，已识别的页面也会继续使用。
- 除非我要求重新生成，否则不要使用 `--force`。

## 6. 转换完成后

1. 查看 `$HOME/Kindle转换/输出/conversion-report.csv`，告诉我：
   - 成功、跳过和失败的数量；
   - 字数明显偏少的书；
   - 目录项很少的书；
   - 识别可信度较低的书。
2. 如果可以，用 epubcheck 检查所有 EPUB。
3. 用访达打开 `$HOME/Kindle转换/输出`。
4. 用简单的话告诉我：
   - EPUB 在“输出/EPUB”，适合用 Send to Kindle 发送；
   - AZW3 在“输出/AZW3”，适合用数据线复制到 Kindle 的 documents 文件夹；
   - 以后新增 PDF 时，只要放进“待转换PDF”文件夹，再让你运行同样的批量转换命令即可。

最后请提醒我：扫描识别仍可能有少量错字，复杂表格、公式、竖排文字和特殊版面可能保留为图片。请先在 Kindle 上抽查几本，再决定是否删除原 PDF。
````

</details>

也可以打开 [prompts/agent-install.zh-CN.md](prompts/agent-install.zh-CN.md) 复制。

## 快速开始

需要 macOS 13+、Python 3.10+ 和 Xcode Command Line Tools。生成 AZW3 还需要 [Calibre](https://calibre-ebook.com/)。

```zsh
xcode-select --install
brew install --cask calibre       # 可选：生成 AZW3
git clone https://github.com/beepony/scan2kindle.git
cd scan2kindle
python3 -m venv .venv             # python3 需为 3.10 或更新版本
.venv/bin/python -m pip install -e .
```

先试转一本的前 30 页：

```zsh
.venv/bin/scan2kindle ~/Books/scans/book.pdf -o /tmp/s2k-test --pages 1-30 --azw3
```

批量转换整个文件夹：

```zsh
.venv/bin/scan2kindle ~/Books/scans -o ~/Books/kindle --azw3
```

不想用终端，也可以双击 `scripts/convert-folder.command` 并选择 PDF 文件夹。

## 输出与传到 Kindle

```text
kindle/
├── EPUB/                  # 用 Send to Kindle 发送
├── AZW3/                  # USB 复制到 Kindle 的 documents 文件夹
├── conversion-report.csv  # 页数、字数、目录数和识别质量
└── .cache/                # OCR 缓存，用于断点续跑
```

## 常用参数

| 参数 | 用途 |
| --- | --- |
| `--azw3` | 同时生成 AZW3（需要 Calibre） |
| `--pages 1-30` | 只转换部分页面，适合试转 |
| `--languages zh-Hant,en-US` | 设置 OCR 语言 |
| `--book-language zh-CN` | 设置电子书语言 |
| `--force` | 重新生成已有电子书 |
| `--no-split-spreads` | 不拆分宽幅扫描页 |

查看全部参数：`.venv/bin/scan2kindle --help`

## 注意

- OCR 仍可能有少量错字；复杂表格、公式和竖排文字通常保留为图片。
- 目前仅支持 macOS。
- 项目不包含任何书籍。请只转换你有权使用的文件，不要上传或分享受版权保护的书籍。

## 许可证

[MIT](LICENSE)
