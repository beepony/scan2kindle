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
