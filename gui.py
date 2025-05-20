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
from dialogs import SshConfigDialog
from dialogs.new_prompt_dialog import NewPromptDialog
from dialogs.edit_prompt_dialog import EditPromptDialog
from widgets import PromptItemWidget

class PromptWindow(QWidget):
    def __init__(self, cfg: dict, data_path: str = "prompt.json"):
        super().__init__()
        self._cfg = cfg
        self._init_paths(data_path)
        self._load_data()
        self._setup_ui()
        self._connect_signals()

    # region ——— 数据初始化与加载
    def _init_paths(self, data_path: str):
        # 运行时资源目录：打包后放在 exe 同目录，否则用当前脚本目录
        if getattr(sys, "frozen", False):
            # PyInstaller 打包后，sys.executable 指向 exe
            base = os.path.dirname(sys.executable)
        else:
            # 开发环境下用脚本目录
            base = os.path.dirname(__file__)
        # 如果 data_path 是相对路径，就放到同目录下
        if not os.path.isabs(data_path):
            self._data_path = os.path.join(base, data_path)
        else:
            self._data_path = data_path

    def _load_data(self):
        # 如果文件不存在，创建一个空的 JSON 文件
        if not os.path.exists(self._data_path):
            empty_dict = {"default": {}}
            with open(self._data_path, 'w', encoding='utf-8') as f:
                json.dump(empty_dict, f, ensure_ascii=False, indent=2)

        with open(self._data_path, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        self.prompt_dict = {}
        self.usage_counts = {}
        for grp, amap in data.items():
            self.prompt_dict[grp] = {}
            self.usage_counts[grp] = {}
            for alias, val in amap.items():
                self.prompt_dict[grp][alias] = val.get('text','')
                self.usage_counts[grp][alias] = val.get('count', 0)
    # endregion

    # region ——— UI 构建
    def _setup_ui(self):
        icon_file = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "icon.png")
        # 设置窗口左上角图标
        self.setWindowIcon(QIcon(icon_file))

        # 窗口设置
        self.setWindowTitle("Prompt Launcher")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # 默认尺寸，设置得更宽松一些
        self.resize(700, 550)
        self.setMinimumSize(400, 300)

        # 如果存在配置文件，恢复上次保存的尺寸
        w, h = self._cfg.get("width"), self._cfg.get("height")
        if isinstance(w, int) and isinstance(h, int):
            self.resize(w, h)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)     # 边距调大
        layout.setSpacing(5)                        # 间距调大
        default_font = QFont("Microsoft YaHei", 12)         # 字体稍微调大

        self.setFont(default_font)

        # 搜索框
        self.search = QLineEdit(placeholderText="搜索 prompt…")
        self.search.setFont(default_font)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search.setContentsMargins(0, 0, 0, 5)
        layout.addWidget(self.search)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setFont(default_font)
        self.tabs.setContentsMargins(0, 0, 0, 0)

        self.tab_lists: dict[str, QListWidget] = {}
        for name in list(self.prompt_dict.keys()):
            self._add_group_tab(name)

        layout.addWidget(self.tabs)

        # 底部按钮：新建、删除分组、上一页、下一页
        btn_new = QPushButton("＋")
        btn_del = QPushButton("－")
        btn_prev = QPushButton("<")
        btn_next = QPushButton(">")
        for btn, slot in [
            (btn_new, self.add_group),
            (btn_del, self.delete_group),
            (btn_prev, self.prev_tab),
            (btn_next, self.next_tab)
        ]:
            btn.setFixedSize(30, 30)
            btn.clicked.connect(slot)

        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_new)
        bottom_layout.addWidget(btn_del)
        bottom_layout.addWidget(btn_prev)
        bottom_layout.addWidget(btn_next)
        # 同步状态显示
        self.sync_label = QLabel("上次同步: -")
        self.sync_label.setFont(self.font())
        # 点击同步状态弹出 SSH 设置对话框
        self.sync_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sync_label.mousePressEvent = lambda ev: self.configure_ssh_backup()
        bottom_layout.insertWidget(0, self.sync_label)

        layout.addWidget(bottom_widget)
    # endregion

    # region ——— 信号绑定
    def _connect_signals(self):
        self.search.textChanged.connect(self.filter_current_tab)

        # 安装事件过滤，实现 Ctrl+C 复制
        for lst in self.tab_lists.values():
            lst.installEventFilter(self)

        # 支持双击标签页重命名
        tab_bar = self.tabs.tabBar()
        tab_bar.installEventFilter(self)
    # endregion

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
        widget = PromptItemWidget(alias, count, self.font())
        item.setSizeHint(widget.sizeHint())
        lst.addItem(item)
        lst.setItemWidget(item, widget)

    def add_group(self):
        # 循环弹窗，直到有效输入或取消
        while True:
            name, ok = QInputDialog.getText(self, "新建分组", "分组名称:")
            if not ok:
                return
            name = name.strip()
            if not name:
                QMessageBox.warning(self, "新建分组", "分组名称不能为空")
                continue
            if name in self.prompt_dict:
                QMessageBox.warning(self, "新建分组", f"分组“{name}”已存在")
                continue
            break
        # 无重名，执行创建
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
        # 循环弹窗，直到有效输入或取消
        while True:
            new_name, ok = QInputDialog.getText(self, "重命名分组", "新名称:", text=old_name)
            if not ok:
                return
            new_name = new_name.strip()
            if not new_name:
                QMessageBox.warning(self, "重命名分组", "新名称不能为空")
                continue
            if new_name == old_name:
                return
            if new_name in self.prompt_dict:
                QMessageBox.warning(self, "重命名分组", f"分组“{new_name}”已存在")
                continue
            break
        # 无重名，执行重命名
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
        # 恢复窗口并激活到前台
        if self.isMinimized() or not self.isVisible():
            self.showNormal()
        # 确保窗口处于活动状态
        self.setWindowState(Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def toggle_window(self):
        """Ctrl+Alt+P 调用，隐藏或显示主窗口"""
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    def edit_prompt(self, item: QListWidgetItem):
        group = self.tabs.tabText(self.tabs.currentIndex())
        widget = self.tab_lists[group].itemWidget(item)
        alias_label = widget.findChild(QLabel)
        old_alias = alias_label.text()
        old_text = self.prompt_dict.get(group, {}).get(old_alias, "")

        dlg = EditPromptDialog(self, old_alias, old_text)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            action, new_alias, new_text = dlg.get_result()
            if action == "delete":
                self._delete_prompt(group, old_alias, item, dlg)
            elif action == "save":
                # 更新数据字典
                if new_alias != old_alias:
                    self.prompt_dict[group].pop(old_alias, None)
                    self.usage_counts[group].pop(old_alias, None)
                self.prompt_dict[group][new_alias] = new_text
                self.usage_counts[group][new_alias] = self.usage_counts[group].get(new_alias, 0)
                # 更新界面
                alias_label.setText(new_alias)
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
        if not lst:
            return
        for i in range(lst.count()):
            item = lst.item(i)
            widget: PromptItemWidget = lst.itemWidget(item)
            if widget.alias_label.text() == alias:
                widget.set_count(self.usage_counts[group][alias])
                break

    def closeEvent(self, event):
        # 关闭时保存当前窗口尺寸
        size = {"width": self.width(), "height": self.height()}
        self._cfg.update(size)
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
        with open(self._data_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    def changeEvent(self, event):
        super().changeEvent(event)
        # 捕获最小化动作，隐藏窗口到托盘
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            # 延迟 hide 保证内部状态切换完成
            QTimer.singleShot(0, self.hide)

    def eventFilter(self, obj, event):
        # 支持双击标签页重命名
        if event.type() == QEvent.Type.MouseButtonDblClick and obj == self.tabs.tabBar():
            mouse_event = event  # QMouseEvent
            idx = obj.tabAt(mouse_event.pos())
            if idx >= 0:
                self.rename_group(idx)
            return True

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
        # 循环弹窗，直到有效输入或取消
        while True:
            dlg = NewPromptDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            alias, content = dlg.get_prompt_data()
            alias = alias.strip()
            # 校验别名
            if not alias:
                QMessageBox.warning(self, "新建 Prompt", "别名不能为空")
                continue
            if alias in self.prompt_dict.get(group, {}):
                QMessageBox.warning(self, "新建 Prompt", f"别名“{alias}”已存在")
                continue
            # 添加新的 prompt 并保存
            self.prompt_dict.setdefault(group, {})[alias] = content
            self.usage_counts.setdefault(group, {})[alias] = 0
            lst = self.tab_lists[group]
            self._add_prompt_item(lst, alias, content, 0)
            self._save()
            break

    def configure_ssh_backup(self):
        dlg = SshConfigDialog(self, self._cfg.get("ssh", {}))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._cfg["ssh"] = dlg.get_config()
            QMessageBox.information(self, "SSH 设置", "SSH 备份设置已保存")

    def update_sync_status(self, timestamp, success: bool):
        """供 SshBackupManager 调用，更新同步状态标签"""
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        result = "成功" if success else "失败"
        self.sync_label.setText(f"上次同步: {ts_str} ({result})")
