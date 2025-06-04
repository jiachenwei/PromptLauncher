# Prompt Launcher

<div align="center">
  <img src="icon.png" alt="Prompt Launcher 图标" width="200">
</div>

<div align="center">
  <img src="https://github.com/jiachenwei/PromptLauncher/actions/workflows/build.yml/badge.svg" alt="GitHub Actions 状态">
</div>

[English README](README_EN.md)

**Prompt Launcher** 是一个基于 PyQt6 的桌面应用程序，用于管理和快速访问自定义的 Prompt。

## 功能特点

- **分组管理**：支持创建、删除和重命名分组。
- **Prompt 搜索**：快速搜索当前分组中的 Prompt。
- **热键支持**：通过全局热键快速显示或隐藏主窗口。
- **使用计数**：记录每个 Prompt 的使用次数。
- **托盘图标**：支持从系统托盘快速访问。
- **SSH 备份**：通过 SSH/SFTP 定时备份 Prompt 数据，并在界面底部显示最近同步时间及状态。

## 安装

### 环境准备

1. 创建并激活 Python 环境：

   ```bash
   conda create -n pyqt6_env python=3.10
   conda activate pyqt6_env
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 安装 PyInstaller：

   ```bash
   pip install pyinstaller
   ```

### 打包应用

使用以下命令打包应用程序：

```bash
pyinstaller PromptLauncher.spec
```

打包完成后，生成的可执行文件位于 `dist/PromptLauncher/` 目录下。

## 使用方法

1. 启动应用程序后，主窗口会显示所有分组和对应的 Prompt。
2. 使用搜索框快速查找 Prompt。
3. 双击 Prompt 可编辑内容。
4. 通过托盘图标或全局热键（默认 `Ctrl+Alt+P`）快速显示或隐藏主窗口。

## 项目结构

```plaintext
PromptLauncher/
├── promptlauncher/                # 核心代码包
│   ├── __init__.py
│   ├── main.py                    # 程序入口
│   ├── gui.py                     # 主窗口逻辑
│   ├── tray.py                    # 托盘图标逻辑
│   ├── hotkey.py                  # 全局热键管理
│   ├── ssh_backup.py              # SSH 备份管理
│   ├── dialogs/                   # 对话框模块
│   │   ├── new_prompt_dialog.py
│   │   ├── edit_prompt_dialog.py
│   │   ├── ssh_config_dialog.py
│   │   └── custom_hotkey_dialog.py
│   └── widgets/                   # 自定义控件模块
│       └── prompt_item_widget.py
├── requirements.txt              # 依赖列表
├── PromptLauncher.spec           # PyInstaller 打包配置
├── icon.png                      # 应用图标
└── README.md                     # 项目说明文档
```

## 许可证

本项目基于 [Apache License](LICENSE) 开源。
