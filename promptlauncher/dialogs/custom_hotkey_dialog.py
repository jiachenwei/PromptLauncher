from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QKeySequenceEdit, QDialogButtonBox

class CustomHotkeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(parent.font() if parent else None)
        self.setWindowTitle("设置快捷热键")
        self.setFont(parent.font())

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请按下想要设置的热键组合："))

        self.seq_edit = QKeySequenceEdit()
        layout.addWidget(self.seq_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(btns)

        # 将 OK 按钮设为默认，回车时触发 accepted
        ok_btn = btns.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)

        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def get_hotkey(self) -> str | None:
        seq = self.seq_edit.keySequence().toString()
        return seq if seq else None
