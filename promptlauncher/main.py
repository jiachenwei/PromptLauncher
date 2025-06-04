# main.py
import os, sys, json, keyboard, ctypes
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from promptlauncher.gui import PromptWindow
from promptlauncher.tray import create_tray
from promptlauncher.hotkey import get_custom_hotkey
from promptlauncher.ssh_backup import SshBackupManager
from promptlauncher.logging_config import setup_logging

logger = logging.getLogger(__name__)

BASE = getattr(sys, "frozen", False) and os.path.dirname(sys.executable) or os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, ".config")
DATA_PATH   = os.path.join(BASE, "prompt.json")
ICON_FILE   = os.path.join(BASE, "icon.png")
INSTANCE_KEY = 'PromptLauncherSingleton'

class ConfigManager:
    def __init__(self, path):
        self._path = path
        self.cfg = self._load()

    def _load(self):
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save(self):
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except:
            pass

    @property
    def hotkey(self):
        return self.cfg.get("hotkey", "ctrl+alt+p").lower()

    @hotkey.setter
    def hotkey(self, seq):
        self.cfg["hotkey"] = seq.lower()

def init_single_instance(key: str):
    """Ensure only one instance of the app runs.

    On Windows we keep the previous mutex based approach. On other
    platforms, ``QLocalServer`` itself is enough to detect another
    running instance.  If another instance is found we notify it via
    ``QLocalSocket`` and exit.
    """

    if os.name == "nt":
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, key)
        is_primary = ctypes.windll.kernel32.GetLastError() != 183
        channel = key + "_IPC"
        if not is_primary:
            sock = QLocalSocket()
            sock.connectToServer(channel)
            if sock.waitForConnected(500):
                sock.write(b"activate")
                sock.flush()
            sys.exit(0)
        # Remove stale server and start listening
        QLocalServer.removeServer(channel)
        server = QLocalServer()
        server.listen(channel)
        return server

    # Non-Windows: use QLocalServer alone
    QLocalServer.removeServer(key)
    server = QLocalServer()
    if not server.listen(key):
        sock = QLocalSocket()
        sock.connectToServer(key)
        if sock.waitForConnected(500):
            sock.write(b"activate")
            sock.flush()
        sys.exit(0)
    return server

class HotkeyManager:
    def __init__(self, cfg: ConfigManager, window: PromptWindow):
        self.cfg = cfg
        self.window = window
        self.handle = None
        self.register(self.cfg.hotkey)

    def _toggle(self):
        QTimer.singleShot(0, self.window.toggle_window)

    def register(self, seq: str):
        if self.handle:
            keyboard.remove_hotkey(self.handle)
        self.handle = keyboard.add_hotkey(seq, self._toggle)

    def on_custom(self):
        new_seq = get_custom_hotkey(self.window)
        if not new_seq:
            return
        self.register(new_seq.lower())
        self.cfg.hotkey = new_seq
        return new_seq

def main():
    setup_logging()
    logger.info("PromptLauncher starting")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(ICON_FILE))

    cfg_mgr = ConfigManager(CONFIG_PATH)
    window  = PromptWindow(cfg_mgr.cfg, DATA_PATH)

    # 初始化定时 SSH 备份管理
    ssh_cfg = cfg_mgr.cfg.get("ssh", {})
    if ssh_cfg.get("host"):
        # 把 window 传给备份管理，以便更新同步状态
        backup_mgr = SshBackupManager(ssh_cfg, DATA_PATH, window)

    # 单例检查并启动 IPC 服务，返回服务实例
    server = init_single_instance(INSTANCE_KEY)
    # 连接 IPC 唤醒（收到 activate 信号时显示主窗口）
    server.newConnection.connect(lambda: window.show_window())

    hot_mgr = HotkeyManager(cfg_mgr, window)
    tray = create_tray(
        app,
        window.show_window,
        hot_mgr.cfg.hotkey.upper(),
        lambda: on_custom_wrapper(hot_mgr, tray, cfg_mgr),
    )
    app.aboutToQuit.connect(cfg_mgr.save)

    window.show_window()
    ret = app.exec()
    cfg_mgr.save()
    logger.info("PromptLauncher exiting")
    sys.exit(ret)

def on_custom_wrapper(hot_mgr, tray, cfg_mgr):
    new_seq = hot_mgr.on_custom()
    if new_seq and tray:
        tray.hotkey_action.setText(f"热键: {new_seq.upper()}")

if __name__ == "__main__":
    main()
