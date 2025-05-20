from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from PyQt6.QtCore import Qt

class SshConfigDialog(QDialog):
    def __init__(self, parent, ssh_cfg):
        super().__init__(parent)
        self.setWindowTitle("SSH 备份设置")
        self.setFont(parent.font())
        self.ssh_cfg = ssh_cfg
        self.fields = {}

        layout = QVBoxLayout(self)
        for label_text, key, default in [
            ("主机:", "host", ""),
            ("端口:", "port", "22"),
            ("用户名:", "user", ""),
            ("远程路径:", "remote_path", ""),
            ("私钥路径:", "key_path", ""),
            ("备份间隔(秒):", "interval", "3600"),
        ]:
            val = ssh_cfg.get(key, default)
            layout.addWidget(QLabel(label_text))
            line = QLineEdit(val)
            line.setFont(parent.font())
            layout.addWidget(line)
            self.fields[key] = line
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(btn_box, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        self.resize(400, 200)
        # self.setLayout(layout)

    def get_config(self):
        return {k: v.text().strip() for k, v in self.fields.items()}
