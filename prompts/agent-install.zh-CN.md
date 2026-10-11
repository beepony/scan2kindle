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
