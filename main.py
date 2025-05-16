# main.py
import os, sys, keyboard, json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from gui import PromptWindow
from tray import create_tray
from hotkey_dialog import get_custom_hotkey

# 运行时资源目录：打包后放在 exe 同目录，否则用脚本目录
if getattr(sys, "frozen", False):
    base = os.path.dirname(sys.executable)
else:
    base = os.path.dirname(__file__)

# 配置文件路径（.config）和 prompt.json 都放在 exe 同目录
CONFIG_PATH = os.path.join(base, ".config")
icon_file = os.path.join(base, "icon.png")

def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
# 设置全局应用图标
app.setWindowIcon(QIcon(icon_file))

window = PromptWindow()

def _hotkey_toggle():
    QTimer.singleShot(0, window.toggle_window)

# 读取默认热键
cfg = _load_config()
HOTKEY = cfg.get("hotkey", "ctrl+alt+p").lower()
hotkey_handle = keyboard.add_hotkey(HOTKEY, _hotkey_toggle)

# 自定义热键回调
def on_custom_hotkey():
    global HOTKEY, hotkey_handle, tray, cfg
    new_seq = get_custom_hotkey(window)
    if not new_seq:
        return
    keyboard.remove_hotkey(hotkey_handle)
    HOTKEY = new_seq.lower()
    hotkey_handle = keyboard.add_hotkey(HOTKEY, _hotkey_toggle)
    # 更新托盘菜单文字
    tray.hotkey_action.setText(f"热键: {new_seq.upper()}")
    # 保存到配置文件
    cfg["hotkey"] = HOTKEY
    _save_config(cfg)

# 创建托盘
tray = create_tray(app, window.show_window, HOTKEY.upper(), on_custom_hotkey)
window.show_window()

sys.exit(app.exec())
