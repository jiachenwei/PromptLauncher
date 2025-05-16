import os, sys
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon

def create_tray(app, show_cb, hotkey="Ctrl+Alt+P", custom_cb=None):
    # 兼容打包后临时目录
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    icon_file = os.path.join(base, "icon.png")
    tray = QSystemTrayIcon(QIcon(icon_file), app)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available")
        return tray

    menu = QMenu()

    # 顶部显示热键
    hotkey_action = menu.addAction(f"热键: {hotkey}")
    hotkey_action.setEnabled(False)
    menu.addSeparator()

    action_show = menu.addAction("打开 Prompt 工具")
    action_custom = menu.addAction("自定义热键")
    action_exit = menu.addAction("退出")

    action_show.triggered.connect(show_cb)
    if custom_cb:
        action_custom.triggered.connect(custom_cb)
    action_exit.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.setToolTip("Prompt Launcher")
    tray.setVisible(True)

    # 双击托盘图标恢复主窗口
    tray.activated.connect(
        lambda reason: show_cb()
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    )

    # 把 action 引用打包到 tray 里，便于外部更新文字
    tray.hotkey_action = hotkey_action
    return tray
