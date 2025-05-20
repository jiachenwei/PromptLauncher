from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDialogButtonBox, QPushButton, QHBoxLayout

class EditPromptDialog(QDialog):
    def __init__(self, parent=None, alias: str = "", text: str = ""):
        super().__init__(parent)
        self.setFont(parent.font())
        self.setWindowTitle("编辑 Prompt")
        self.result_action = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("别名:"))
        self.inp_alias = QLineEdit(alias)
        self.inp_alias.setFont(parent.font())
        layout.addWidget(self.inp_alias)

        layout.addWidget(QLabel("内容:"))
        self.editor = QTextEdit()
        self.editor.setFont(parent.font())
        self.editor.setPlainText(text)
        layout.addWidget(self.editor)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_btn = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("保存")
        delete_btn = QPushButton("删除")
        delete_btn.setFont(parent.font())
        delete_btn.clicked.connect(self._on_delete)
        
        # 同步按钮尺寸
        ok_size = ok_btn.sizeHint()
        del_size = delete_btn.sizeHint()
        btn_w = max(ok_size.width(), del_size.width())
        btn_h = ok_size.height()
        ok_btn.setFixedSize(btn_w, btn_h)
        delete_btn.setFixedSize(btn_w, btn_h)

        hbox = QHBoxLayout()
        hbox.addWidget(btn_box)
        hbox.addWidget(delete_btn)
        layout.addLayout(hbox)

        btn_box.accepted.connect(self._on_save)

    def _on_save(self):
        self.result_action = "save"
        self.accept()

    def _on_delete(self):
        self.result_action = "delete"
        self.accept()

    def get_result(self):
        alias = self.inp_alias.text().strip()
        text = self.editor.toPlainText().strip()
        return self.result_action, alias, text
