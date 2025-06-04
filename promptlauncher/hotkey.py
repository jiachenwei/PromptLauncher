from PyQt6.QtWidgets import QDialog
from .dialogs import CustomHotkeyDialog


def get_custom_hotkey(parent=None) -> str | None:
    """
    弹出对话框，捕获用户按下的热键组合，
    返回类似 "Ctrl+Alt+P" 的字符串，或 None（取消）。
    """
    dlg = CustomHotkeyDialog(parent)
    
    if dlg.exec() == QDialog.DialogCode.Accepted:
        return dlg.get_hotkey()
    return None
