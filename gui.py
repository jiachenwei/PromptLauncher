import os, sys, json
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QApplication,
    QVBoxLayout, QLineEdit,
    QTabWidget, QListWidget, QListWidgetItem,
    QSizePolicy, QPushButton, QHBoxLayout, QLabel,
    QDialog, QTextEdit, QDialogButtonBox, QInputDialog, QMessageBox, QMenu
)

class PromptWindow(QWidget):
    def __init__(self, data_path: str = "prompt.json"):
        super().__init__()

        # PyInstaller 解包后资源目录
        base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
        # 如果 data_path 是相对路径，就放到同目录下
        if not os.path.isabs(data_path):
            self.data_path = os.path.join(base, data_path)
        else:
            self.data_path = data_path

        icon_file = os.path.join(base, "icon.png")
        # 设置窗口左上角图标
        self.setWindowIcon(QIcon(icon_file))

        # —— 读取 prompt.json（含 text/count）或使用传入的 prompt_dict 初始化 —— 
        
        if not os.path.exists(self.data_path):
            # 如果文件不存在，创建一个空的 JSON 文件
            empty_dict = {"default": {}}
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(empty_dict, f, ensure_ascii=False, indent=2)

        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        self.prompt_dict = {}
        self.usage_counts = {}
        for grp, amap in data.items():
            self.prompt_dict[grp] = {}
            self.usage_counts[grp] = {}
            for alias, val in amap.items():
                self.prompt_dict[grp][alias] = val.get('text','')
                self.usage_counts[grp][alias] = val.get('count', 0)

        # 记忆窗口尺寸的配置文件路径（JSON）
        self._cfg_path = os.path.join(os.path.dirname(self.data_path), ".config")

        # 窗口设置
        self.setWindowTitle("Prompt Launcher")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # 默认尺寸
        self.resize(600, 450)
        self.setMinimumSize(350, 250)

        # 如果存在配置文件，恢复上次保存的尺寸
        if os.path.exists(self._cfg_path):
            try:
                with open(self._cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    w, h = cfg.get("width"), cfg.get("height")
                    if isinstance(w, int) and isinstance(h, int):
                        self.resize(w, h)
            except Exception as e:
                print(f"Error loading config: {e}")
                pass

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        default_font = QFont("Segoe UI", 11)
        self.setFont(default_font)

        # 搜索框
        self.search = QLineEdit(placeholderText="搜索 prompt…")
        self.search.setFont(default_font)
        self.search.textChanged.connect(self.filter_current_tab)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.search)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setFont(default_font)
        self.tabs.setContentsMargins(0, 0, 0, 0)

        self.tab_lists: dict[str, QListWidget] = {}
        for name in list(self.prompt_dict.keys()):
            self._add_group_tab(name)

        # 安装事件过滤，实现 Ctrl+C 复制
        for lst in self.tab_lists.values():
            lst.installEventFilter(self)

        # 按钮：新建、删除分组、上一页、下一页
        btn_new = QPushButton("＋")
        btn_new.setFixedSize(20, 20)
        btn_new.clicked.connect(self.add_group)
        btn_del = QPushButton("－")
        btn_del.setFixedSize(20, 20)
        btn_del.clicked.connect(self.delete_group)
        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(20, 20)
        btn_prev.clicked.connect(self.prev_tab)
        btn_next = QPushButton(">")
        btn_next.setFixedSize(20, 20)
        btn_next.clicked.connect(self.next_tab)

        corner = QWidget()
        corner_layout = QHBoxLayout(corner)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(2)
        corner_layout.addWidget(btn_new)
        corner_layout.addWidget(btn_del)
        corner_layout.addWidget(btn_prev)
        corner_layout.addWidget(btn_next)
        self.tabs.setCornerWidget(corner, Qt.Corner.TopRightCorner)

        # 双击标签重命名
        self.tabs.tabBar().tabBarDoubleClicked.connect(self.rename_group)

        layout.addWidget(self.tabs)

    def _add_group_tab(self, group_name: str):
        alias_map = self.prompt_dict.get(group_name, {})
        lst = QListWidget()
        lst.setFont(self.font())
        lst.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lst.setUniformItemSizes(True)
        # 双击进入编辑
        lst.itemDoubleClicked.connect(self.edit_prompt)
        # 右键菜单：新建 Prompt
        lst.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        lst.customContextMenuRequested.connect(
            lambda pos, grp=group_name, lw=lst: self._show_prompt_context_menu(grp, lw, pos)
        )
        for alias, text in alias_map.items():
            cnt = self.usage_counts.get(group_name, {}).get(alias, 0)
            self._add_prompt_item(lst, alias, text, cnt)
        self.tab_lists[group_name] = lst
        self.tabs.addTab(lst, group_name)

    def _add_prompt_item(self, lst: QListWidget, alias: str, prompt_text: str, count: int):
        item = QListWidgetItem()
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 4, 8, 4)
        vbox.setSpacing(2)

        alias_label = QLabel(alias)
        alias_font = QFont(self.font())
        alias_font.setBold(True)
        alias_label.setFont(alias_font)

        # 名称和计数水平布局，计数靠右
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(alias_label)
        hbox.addStretch()
        cnt_label = QLabel(str(count))
        cnt_label.setFont(self.font())
        cnt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        # 标记一下，方便后面查找
        cnt_label.setObjectName(f"cnt_{alias}")
        hbox.addWidget(cnt_label)
        vbox.addLayout(hbox)

        # 固定高度（包含计数行）
        widget.setFixedHeight(widget.sizeHint().height())
        item.setSizeHint(widget.sizeHint())
        lst.addItem(item)
        lst.setItemWidget(item, widget)

    def add_group(self):
        name, ok = QInputDialog.getText(self, "新建分组", "分组名称:")
        name = name.strip()
        if ok and name and name not in self.prompt_dict:
            self.prompt_dict[name] = {}
            self.usage_counts[name] = {}
            self._save()
            self._add_group_tab(name)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def delete_group(self):
        idx = self.tabs.currentIndex()
        if idx < 0:
            return
        name = self.tabs.tabText(idx)

        resp = QMessageBox.question(
            self, "删除分组",
            f"确认删除分组“{name}”及其所有提示？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.prompt_dict.pop(name, None)
            self.usage_counts.pop(name, None)
            self._save()
            self.tabs.removeTab(idx)
            self.tab_lists.pop(name, None)

    def rename_group(self, index: int):
        if index < 0:
            return
        old_name = self.tabs.tabText(index)
        new_name, ok = QInputDialog.getText(self, "重命名分组", "新名称:", text=old_name)
        new_name = new_name.strip()
        if ok and new_name and new_name not in self.prompt_dict and new_name != old_name:
            self.prompt_dict[new_name] = self.prompt_dict.pop(old_name)
            self.usage_counts[new_name] = self.usage_counts.pop(old_name)
            self._save()
            self.tabs.setTabText(index, new_name)
            self.tab_lists[new_name] = self.tab_lists.pop(old_name)

    def prev_tab(self):
        idx = self.tabs.currentIndex()
        if idx > 0:
            self.tabs.setCurrentIndex(idx - 1)

    def next_tab(self):
        idx = self.tabs.currentIndex()
        if idx < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(idx + 1)

    def show_window(self):
        # 从托盘或热键唤起时恢复窗口并置顶
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.show()

    def toggle_window(self):
        """Ctrl+Alt+P 调用，隐藏或显示主窗口"""
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    def edit_prompt(self, item: QListWidgetItem):
        group = self.tabs.tabText(self.tabs.currentIndex())
        widget = self.tab_lists[group].itemWidget(item)
        # 只取第一个 QLabel（alias_label）
        alias_label = widget.findChild(QLabel)
        old_alias = alias_label.text()
        # 从数据字典获取原始 prompt 文本
        old_text = self.prompt_dict.get(group, {}).get(old_alias, "")

        dlg = QDialog(self)
        dlg.setWindowTitle("编辑 Prompt")
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(8)

        dlg_layout.addWidget(QLabel("别名:"))
        inp_alias = QLineEdit(old_alias)
        inp_alias.setFont(self.font())
        dlg_layout.addWidget(inp_alias)

        dlg_layout.addWidget(QLabel("内容:"))
        editor = QTextEdit()
        editor.setFont(self.font())
        editor.setPlainText(old_text)
        dlg_layout.addWidget(editor)

        # 按钮布局
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_button = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("保存")
        delete_btn = QPushButton("删除提示")
        delete_btn.setFont(self.font())
        delete_btn.clicked.connect(lambda: self._delete_prompt(group, old_alias, item, dlg))
        delete_btn.setFixedSize(ok_button.sizeHint())
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_box)
        btn_layout.addWidget(delete_btn)
        dlg_layout.addLayout(btn_layout)
        btn_box.accepted.connect(dlg.accept)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_alias = inp_alias.text().strip()
            new_text = editor.toPlainText().strip()
            # 更新数据字典
            if new_alias != old_alias:
                self.prompt_dict[group].pop(old_alias, None)
                self.usage_counts[group].pop(old_alias, None)
            self.prompt_dict[group][new_alias] = new_text
            self.usage_counts[group][new_alias] = self.usage_counts[group].get(new_alias, 0)
            # 更新界面上的别名
            alias_label.setText(new_alias)
            # 调整列表项高度
            widget.setFixedHeight(widget.sizeHint().height())
            item.setSizeHint(widget.sizeHint())
            self._save()

    def _delete_prompt(self, group: str, alias: str, item: QListWidgetItem, dialog: QDialog):
        resp = QMessageBox.question(
            self, "删除",
            f"确认删除提示“{alias}”？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            # 删除数据及界面项
            self.prompt_dict[group].pop(alias, None)
            self.usage_counts[group].pop(alias, None)
            list_widget = self.tab_lists[group]
            list_widget.takeItem(list_widget.row(item))
            self._save()
            # 改为 reject()，避免 edit_prompt 在 exec() 后继续保存已删除条目
            dialog.reject()

    def filter_current_tab(self, keyword: str):
        lst = self.tab_lists[self.tabs.tabText(self.tabs.currentIndex())]
        key = keyword.lower()
        for i in range(lst.count()):
            item = lst.item(i)
            widget = lst.itemWidget(item)
            # 只按别名过滤
            alias = widget.findChild(QLabel).text().lower()
            item.setHidden(key not in alias)

    def get_selected_prompt(self) -> str | None:
        group = self.tabs.tabText(self.tabs.currentIndex())
        item = self.tab_lists[group].currentItem()
        if not item:
            return None
        alias = self.tab_lists[group].itemWidget(item).findChild(QLabel).text()
        text = self.prompt_dict[group][alias]
        # 每次取用时自增并保存
        self._increment_usage(group, alias)
        return text

    def _increment_usage(self, group: str, alias: str):
        self.usage_counts[group][alias] += 1
        self._save()
        # 界面上同步更新对应 count 标签
        lst = self.tab_lists.get(group)
        if lst:
            for i in range(lst.count()):
                item = lst.item(i)
                widget = lst.itemWidget(item)
                alias_label = widget.findChild(QLabel)
                if alias_label and alias_label.text() == alias:
                    cnt_label = widget.findChild(QLabel, f"cnt_{alias}")
                    if cnt_label:
                        cnt_label.setText(str(self.usage_counts[group][alias]))
                    break

    def closeEvent(self, event):
        # 关闭时保存当前窗口尺寸
        try:
            size = {"width": self.width(), "height": self.height()}
            with open(self._cfg_path, 'w', encoding='utf-8') as f:
                json.dump(size, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            pass
        # 退出前再保存一次
        self._save()
        event.accept()
        QApplication.quit()

    def _save(self):
        """把 prompt_dict + usage_counts 一起写回 prompt.json"""
        out: dict[str, dict[str, dict[str, int|str]]] = {}
        for grp, amap in self.prompt_dict.items():
            out[grp] = {}
            for alias, text in amap.items():
                cnt = self.usage_counts.get(grp, {}).get(alias, 0)
                out[grp][alias] = {'text': text, 'count': cnt}
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    def changeEvent(self, event):
        super().changeEvent(event)
        # 捕获最小化动作，隐藏窗口到托盘
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            # 延迟 hide 保证内部状态切换完成
            QTimer.singleShot(0, self.hide)

    def eventFilter(self, obj, event):
        # 支持按 Ctrl+C 复制选中 prompt 文本并计数
        if event.type() == QEvent.Type.KeyPress and obj in self.tab_lists.values():
            if (event.key() == Qt.Key.Key_C 
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                group = self.tabs.tabText(self.tabs.currentIndex())
                item = obj.currentItem()
                if item:
                    alias = obj.itemWidget(item).findChild(QLabel).text()
                    text = self.prompt_dict[group][alias]
                    QApplication.clipboard().setText(text)
                    # 复制时计数并写回
                    self._increment_usage(group, alias)
                return True
        return super().eventFilter(obj, event)

    def insert_prompt(self, group: str, item: QListWidgetItem):
        alias = self.tab_lists[group].itemWidget(item).findChild(QLabel).text()
        text = self.prompt_dict[group][alias]
        # 复制到剪贴板并计数
        QApplication.clipboard().setText(text)
        self._increment_usage(group, alias)

    def _show_prompt_context_menu(self, group: str, lst: QListWidget, pos):
        """在列表空白或项上右键，显示新建 Prompt 选项"""
        menu = QMenu(self)
        menu.addAction("新建 Prompt", lambda: self._new_prompt(group))
        menu.exec(lst.mapToGlobal(pos))

    def _new_prompt(self, group: str):
        # 使用自定义对话框支持多行输入
        dlg = QDialog(self)
        dlg.setWindowTitle("新建 Prompt")
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.addWidget(QLabel("别名:"))
        inp_alias = QLineEdit()
        inp_alias.setFont(self.font())
        dlg_layout.addWidget(inp_alias)
        dlg_layout.addWidget(QLabel("内容:"))
        editor = QTextEdit()
        editor.setFont(self.font())
        dlg_layout.addWidget(editor)
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        dlg_layout.addWidget(btn_box)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            alias = inp_alias.text().strip()
            text = editor.toPlainText().strip()
            if not alias or alias in self.prompt_dict.get(group, {}):
                return
            self.prompt_dict.setdefault(group, {})[alias] = text
            self.usage_counts.setdefault(group, {})[alias] = 0
            lst = self.tab_lists[group]
            self._add_prompt_item(lst, alias, text, 0)
            self._save()
