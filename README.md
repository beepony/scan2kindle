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
请帮我在这台 Mac 上安装 https://github.com/beepony/scan2kindle ，并带我完成第一次扫描 PDF 转 Kindle 电子书。

请自动完成能做的步骤，用简短中文汇报进度；只有需要我确认、输入密码或放入 PDF 时再问我。

要求：
- 仅支持 macOS；不要修改、删除或上传我的 PDF 和转换结果。
- 不要用 sudo；遇到权限或沙盒限制时，按当前 AI 工具的规则申请权限。

步骤：
1. 检查并准备环境：Xcode Command Line Tools、Python 3.10+；如需 AZW3，再安装 Calibre。可用 Homebrew 时优先用它安装缺少的软件。
2. 安装工具：
   - 将仓库克隆或更新到 `~/scan2kindle`；
   - 用 Python 3.10+ 创建 `.venv`；
   - 运行 `.venv/bin/python -m pip install -e '.[test]'`；
   - 运行测试确认安装成功。
3. 创建 `~/Kindle转换/待转换PDF`、`~/Kindle转换/输出`、`~/Kindle转换/试转换`，然后在访达中打开“待转换PDF”。请我放入 PDF（可以建子文件夹），并等我回复“已放好”。
4. 用第一本 PDF 的前 30 页试转：

```zsh
cd ~/scan2kindle
.venv/bin/scan2kindle "<PDF 路径>" -o ~/Kindle转换/试转换 --pages 1-30 --azw3 --force
```

5. 试转成功后批量转换：

```zsh
cd ~/scan2kindle
caffeinate -dimsu .venv/bin/scan2kindle ~/Kindle转换/待转换PDF -o ~/Kindle转换/输出 --azw3
```

如果没有 Calibre，以上命令都去掉 `--azw3`。中断后再次运行即可继续。

6. 完成后查看 `conversion-report.csv`，告诉我成功、失败和可能需要检查的书，并打开输出文件夹。说明：
   - `EPUB` 可以用 Send to Kindle 发送；
   - `AZW3` 可以用 USB 复制到 Kindle 的 `documents` 文件夹。
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
