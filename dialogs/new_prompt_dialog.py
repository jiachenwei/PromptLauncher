from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDialogButtonBox

class NewPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(parent.font() if parent else None)
        self.setWindowTitle("新建 Prompt")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("别名:"))
        self.inp_alias = QLineEdit()
        self.layout.addWidget(self.inp_alias)

        self.layout.addWidget(QLabel("内容:"))
        self.editor = QTextEdit()
        self.layout.addWidget(self.editor)

        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.layout.addWidget(self.btn_box)

        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self.reject)

    def get_prompt_data(self):
        alias = self.inp_alias.text().strip()
        content = self.editor.toPlainText().strip()
        return alias, content
