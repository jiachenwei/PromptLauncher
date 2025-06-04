import os, sys
import logging
import json
import urllib.request
import webbrowser
from .logging_config import setup_logging
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from .version import __version__


def _parse_version(ver: str) -> tuple:
    try:
        return tuple(int(p) for p in ver.strip("v").split("."))
    except Exception:
        return (0,)


def check_update(parent=None):
    """Check GitHub releases and prompt to open the download page if newer."""
    # 统一对话框图标路径
    icon_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "icon.png")
    url = "https://api.github.com/repos/jiachenwei/PromptLauncher/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.load(resp)
        latest = data.get("tag_name", "")
        if latest and _parse_version(latest) > _parse_version(__version__):
            dlg = QMessageBox(parent)
            dlg.setWindowTitle("检查更新")
            dlg.setText(f"发现新版本 {latest}，是否前往下载？")
            dlg.setIcon(QMessageBox.Icon.Question)
            dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dlg.setWindowIcon(QIcon(icon_path))
            ret = dlg.exec()
            if ret == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://github.com/jiachenwei/PromptLauncher/releases/latest")
        else:
            dlg = QMessageBox(parent)
            dlg.setWindowTitle("检查更新")
            dlg.setText("当前已是最新版本")
            dlg.setIcon(QMessageBox.Icon.Information)
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
            dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dlg.setWindowIcon(QIcon(icon_path))
            dlg.exec()
    except Exception as e:
        logger.error("update check failed", exc_info=True)
        dlg = QMessageBox(parent)
        dlg.setWindowTitle("检查更新")
        dlg.setText(f"检查更新失败: {e}")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setWindowIcon(QIcon(icon_path))
        dlg.exec()

logger = logging.getLogger(__name__)
setup_logging()

def create_tray(app, show_cb, hotkey="Ctrl+Alt+P", custom_cb=None):
    """Create and return the system tray icon.

    If the current platform does not support a system tray, ``None`` is
    returned so callers can handle the absence of a tray icon gracefully.
    """
    # 兼容打包后临时目录
    icon_file = os.path.join(
        getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "icon.png"
    )

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.warning("System tray not available")
        return None

    tray = QSystemTrayIcon(QIcon(icon_file), app)

    menu = QMenu()

    # 顶部显示热键
    hotkey_action = menu.addAction(f"热键: {hotkey}")
    hotkey_action.setEnabled(False)
    menu.addSeparator()

    action_show = menu.addAction("打开 Prompt 工具")
    action_custom = menu.addAction("自定义热键")
    action_update = menu.addAction("检查更新")
    action_about = menu.addAction("关于")            # ← 新增“关于”菜单项
    menu.addSeparator()                            # ← 分隔线
    action_exit = menu.addAction("退出")

    action_show.triggered.connect(show_cb)
    if custom_cb:
        action_custom.triggered.connect(custom_cb)
    action_update.triggered.connect(lambda: check_update())

    # 把“关于”改为自定义弹窗，使用自定义 icon
    def _show_about():
        icon_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "icon.png")
        
        # 准备对话框
        dlg = QDialog()
        dlg.setFont(app.font())
        # 设置窗口左上角图标
        dlg.setWindowIcon(QIcon(icon_path))
        dlg.setWindowTitle("关于 Prompt Launcher")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setFixedSize(320, 240)  # 设置固定大小，避免用户调整窗口大小

        # 布局
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # 图标
        pix = QPixmap(icon_path)
        dpr = QApplication.primaryScreen().devicePixelRatio()
        size = int(64 * dpr)  # ← 确保是整数
        pix.setDevicePixelRatio(dpr)
        pix = pix.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        lbl_icon = QLabel()
        lbl_icon.setPixmap(pix)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon)

        # 文字
        lbl_text = QLabel(
            "<h3>Prompt Launcher</h3>"
            "<p>作者：jiachenwei<br>"
            "<a href='https://github.com/jiachenwei'>GitHub 主页</a><br>"
            "License: MIT License</p>"
        )
        lbl_text.setTextFormat(Qt.TextFormat.RichText)
        lbl_text.setOpenExternalLinks(True)
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_text)

        # 按钮
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(dlg.accept)
        btn_ok.setFixedWidth(80)
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(btn_ok)
        hbox.addStretch()
        layout.addLayout(hbox)

        dlg.exec()

    action_about.triggered.connect(_show_about)
    action_exit.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.setToolTip("Prompt Launcher")
    tray.setVisible(True)

    # 双击或单击托盘图标恢复主窗口
    tray.activated.connect(
        lambda reason: show_cb()
            if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                          QSystemTrayIcon.ActivationReason.DoubleClick)
            else None
    )

    # 把 action 引用打包到 tray 里，便于外部更新文字
    tray.hotkey_action = hotkey_action
    return tray
