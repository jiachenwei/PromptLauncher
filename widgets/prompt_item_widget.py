from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

class PromptItemWidget(QWidget):
    def __init__(self, alias: str, count: int, font):
        super().__init__()
        self.alias_label = QLabel(alias)
        self.alias_label.setFont(font)

        self.count_label = QLabel(str(count))
        self.count_label.setFont(font)
        # 方便 findChild 时也能定位到
        self.count_label.setObjectName("cnt_label")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.addWidget(self.alias_label)
        layout.addStretch()
        layout.addWidget(self.count_label)

    def set_count(self, count: int):
        """外部调用以更新计数并自适应高度"""
        self.count_label.setText(str(count))
        self.setFixedHeight(self.sizeHint().height())
