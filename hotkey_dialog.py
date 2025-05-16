from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QKeySequenceEdit, QDialogButtonBox
)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt

def get_custom_hotkey(parent=None) -> str | None:
    """
    弹出对话框，捕获用户按下的热键组合，
    返回类似 "Ctrl+Alt+P" 的字符串，或 None（取消）。
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle("设置快捷热键")
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("请按下想要设置的热键组合："))

    seq_edit = QKeySequenceEdit()
    layout.addWidget(seq_edit)

    btns = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok |
        QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(btns)

    # 将 OK 按钮设为默认，回车时触发 accepted
    ok_btn = btns.button(QDialogButtonBox.StandardButton.Ok)
    ok_btn.setDefault(True)
    ok_btn.setAutoDefault(True)

    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        hs = seq_edit.keySequence().toString()
        return hs if hs else None
    return None