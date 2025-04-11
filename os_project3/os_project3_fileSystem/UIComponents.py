'''
------------------------------------------------------
文件名: UIComponents.py
描述: 用户界面组件模块
包含: attributeForm类（属性视图）
      editForm类（文件编辑视图）
      File_Widget类（文件/文件夹显示组件）
      CustomTooltip类（自定义悬浮提示框）
功能: 提供文件系统界面的各种UI交互组件
------------------------------------------------------
'''

import os
import time
import re
from typing import Optional
import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# 定义类：属性视图
class attributeForm(QWidget): 
    def __init__(self, name, isFile, createTime, updateTime, size, child = 0):
        super().__init__()

        # 设置提示框信息
        self.name = name
        self.setWindowTitle('attribute')
        self.setWindowIcon(QIcon('images/attribute.png'))
        self.resize(350, 220)  
        layout = QVBoxLayout()

        if isFile: 
            self.icon = QPixmap('images/file.png')
        else:
            self.icon = QPixmap('images/folder.png')

        fileType = QLabel(self)
        if isFile:
            fileType.setText('Type: file')
        else:
            fileType.setText('Type: folder')
        fileType.setFont(QFont('Times New Roman', 10))
        layout.addWidget(fileType)

        # 文件/文件夹名称
        fileName = QLabel(self)
        fileName.setText('Name: ' + self.name)
        fileName.setFont(QFont('Times New Roman', 10))
        layout.addWidget(fileName)

        # 文件/文件夹大小
        sizeLabel = QLabel(self)
        if size < 1024:
            sizeLabel.setText('Size: ' + str(size) + ' B')
        elif size < 1024 * 1024:
            sizeLabel.setText('Size: ' + str(round(size / 1024, 2)) + ' KB')
        else:
            sizeLabel.setText('Size: ' + str(round(size / (1024 * 1024), 2)) + ' MB')
        sizeLabel.setFont(QFont('Times New Roman', 10))
        layout.addWidget(sizeLabel)

        # 文件/文件夹创建时间
        createLabel = QLabel(self)
        year = str(createTime.tm_year)
        month = str(createTime.tm_mon)
        day = str(createTime.tm_mday)
        hour = str(createTime.tm_hour)
        hour = hour.zfill(2)
        minute = str(createTime.tm_min)
        minute = minute.zfill(2)
        second = str(createTime.tm_sec)
        second = second.zfill(2)
        createLabel.setText('Create Time: ' + year + '.' + month + '.' + day + '. ' + hour + ':' + minute + ':' + second)
        createLabel.setFont(QFont('Times New Roman', 10))
        layout.addWidget(createLabel)

        # 文件更新时间
        if isFile: 
            updateLabel = QLabel(self)
            year = str(updateTime.tm_year)
            month = str(updateTime.tm_mon)
            day = str(updateTime.tm_mday)
            hour = str(updateTime.tm_hour)
            hour = hour.zfill(2)
            minute = str(updateTime.tm_min)
            minute = minute.zfill(2)
            second = str(updateTime.tm_sec)
            second = second.zfill(2)
            updateLabel.setText('update time：' + year + '.' + month + '.' + day + '. ' + hour + ':' + minute + ':' + second)
            updateLabel.setFont(QFont('Times New Roman', 10))
            layout.addWidget(updateLabel)

        # 文件夹下的项目数量
        else:
            updateLabel = QLabel(self)
            updateLabel.setText('Number of items in the catalog:' + str(child) )
            updateLabel.setFont(QFont('Times New Roman', 10))
            layout.addWidget(updateLabel)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)

# 定义类：编辑视图
class editForm(QWidget):
    _signal = PyQt5.QtCore.pyqtSignal(str) 

    def __init__(self, name, data):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(name)
        self.name = name
        self.setWindowIcon(QIcon('images/file.png'))

        # 打开文件输入内容
        self.resize(900, 600)
        self.text_edit = QTextEdit(self)  
        self.text_edit.setText(data)  
        self.text_edit.setFont(QFont("Times New Roman", 10))
        self.text_edit.setPlaceholderText("Enter the file content:")  
        self.initialData = data

        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.text_edit)
        self.v_layout.addLayout(self.h_layout)
        self.setLayout(self.v_layout)
        self.setWindowModality(PyQt5.QtCore.Qt.ApplicationModal)

    # 关闭文件系统
    def closeEvent(self, event): 
        if self.initialData == self.text_edit.toPlainText(): 
            event.accept()
            return
        
        # 是否写入磁盘
        reply = QMessageBox()
        reply.setFont(QFont("Times New Roman", 11))
        reply.setWindowTitle('warning')
        reply.setWindowIcon(QIcon("images/warning.png"))
        reply.setText('Whether to save the modification?')
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Ignore)
        buttonY = reply.button(QMessageBox.Yes)
        buttonY.setText('yes')
        buttonN = reply.button(QMessageBox.No)
        buttonN.setText('no')
        buttonI = reply.button(QMessageBox.Ignore)
        buttonI.setText('cancel')
        reply.exec_()

        if reply.clickedButton() == buttonI:
            event.ignore()
        elif reply.clickedButton() == buttonY:
            self._signal.emit(self.text_edit.toPlainText())
            event.accept()
        else:
            event.accept()

    def changeMessage(self): 
        pass

# 定义类：每个文件/文件夹视图
class File_Widget(QListWidget): 
    def __init__(self, curNode, parents, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.edited_item = self.currentItem()
        self.close_flag = True
        self.currentItemChanged.connect(self.close_edit)
        self.curNode = curNode
        self.parents = parents
        self.isEdit = False
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 创建自定义悬浮框
        self.custom_tooltip = CustomTooltip(self)
        
        # 跟踪上一次悬停的项目
        self.last_hovered_item = None
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.showItemTooltip)
        
        # 用于追踪鼠标是否离开了控件
        self.leave_timer = QTimer()
        self.leave_timer.setSingleShot(True)
        self.leave_timer.timeout.connect(self.hideTooltipIfNeeded)
        
        # 监听模型变更，以便在视图改变时重置悬浮状态
        self.model().rowsRemoved.connect(self.resetHoverState)
        self.model().modelReset.connect(self.resetHoverState)
        
    # 重置悬浮状态
    def resetHoverState(self):
        self.last_hovered_item = None
        self.hover_timer.stop()
        if self.custom_tooltip.isVisible():
            self.custom_tooltip.hideTooltip()
        
    # 当鼠标移动时跟踪悬停项目
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        item = self.itemAt(event.pos())
        
        # 重置离开定时器
        self.leave_timer.stop()
        
        # 如果鼠标移动到新项目上
        if item != self.last_hovered_item:
            # 如果之前有悬停的项目，隐藏工具提示
            if self.last_hovered_item and self.custom_tooltip.isVisible():
                self.custom_tooltip.hideTooltip()
                
            self.last_hovered_item = item
            self.hover_timer.stop()
            
            if item:
                # 延迟显示工具提示，使体验更自然
                self.hover_timer.start(500)  # 500毫秒延迟
    
    # 当鼠标离开控件
    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        # 设置一个短暂的延迟，以防鼠标只是短暂地离开然后又回来
        self.leave_timer.start(200)
    
    # 隐藏工具提示如果需要
    def hideTooltipIfNeeded(self):
        # 如果鼠标真的离开了控件
        if self.custom_tooltip.isVisible():
            self.custom_tooltip.hideTooltip()
        self.last_hovered_item = None
    
    # 显示项目工具提示
    def showItemTooltip(self):
        # 安全检查：确保last_hovered_item仍然有效
        if not self.last_hovered_item:
            return
            
        try:
            # 尝试访问text属性来检查项目是否有效
            item_text = self.last_hovered_item.text()
            
            # 找到对应的节点
            node = None
            for child in self.curNode.children:
                if child.name == item_text:
                    node = child
                    break
                    
            if node:
                # 生成工具提示内容
                tooltip_content = self.createTooltipForNode(node)
                
                # 再次检查项目是否仍然有效
                try:
                    # 获取项目的全局位置
                    item_rect = self.visualItemRect(self.last_hovered_item)
                    global_pos = self.mapToGlobal(item_rect.bottomRight())
                    # 显示自定义工具提示
                    self.custom_tooltip.showTooltip(tooltip_content, global_pos)
                except:
                    # 项目可能在中途被删除
                    self.last_hovered_item = None
                    if self.custom_tooltip.isVisible():
                        self.custom_tooltip.hideTooltip()
                    
        except Exception as e:
            # 如果访问属性出错，说明对象已无效
            self.last_hovered_item = None
            if self.custom_tooltip.isVisible():
                self.custom_tooltip.hideTooltip()

    # 为节点创建悬浮提示内容
    def createTooltipForNode(self, node):
        # 获取类型
        node_type = "File" if node.isFile else "Folder"
        
        # 获取大小
        if node.isFile:
            size = len(node.data.read(self.parents.fat, self.parents.disk))
            if size < 1024:
                size_str = f"{size} Bytes"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            else:
                size_str = f"{size/(1024*1024):.2f} MB"
        else:
            size = self.parents.getSize(node)
            if size < 1024:
                size_str = f"{size} Bytes"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            else:
                size_str = f"{size/(1024*1024):.2f} MB"
        
        # 获取修改日期
        year = str(node.updateTime.tm_year)
        month = str(node.updateTime.tm_mon).zfill(2)
        day = str(node.updateTime.tm_mday).zfill(2)
        hour = str(node.updateTime.tm_hour).zfill(2)
        minute = str(node.updateTime.tm_min).zfill(2)
        
        mod_time = f"{year}-{month}-{day} {hour}:{minute}"
        
        # 创建适合深灰色背景的HTML内容
        tooltip = f"""
        <p style='margin:5px 0; color:white;'><b>Type:</b> {node_type}</p>
        <p style='margin:5px 0; color:white;'><b>Size:</b> {size_str}</p>
        <p style='margin:5px 0; color:white;'><b>Modified:</b> {mod_time}</p>
        """
        return tooltip

    # 回车按下时编辑完成
    def keyPressEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Return:
            if self.close_flag:
                self.close_edit()
            self.close_flag = True

    # 编辑新文件
    def edit_new_item(self) -> None:
        self.close_flag = False
        self.close_edit()
        count = self.count()
        self.addItem('')
        item = self.item(count)
        self.edited_item = item
        self.openPersistentEditor(item)
        self.editItem(item)

    # 双击打开
    def item_double_clicked(self, modelindex: QModelIndex) -> None:
        return

    # 编辑文件
    def editLast(self, index = -1) -> None:
        self.close_edit()
        item = self.item(self.count() - 1)
        self.setCurrentItem(item)
        self.edited_item = item
        self.openPersistentEditor(item)
        self.editItem(item)
        self.isEdit = True
        self.index = index

    # 选择编辑
    def editSelected(self, index) -> None:
        self.close_edit()
        item = self.selectedItems()[-1]
        self.setCurrentItem(item)
        self.edited_item = item
        self.openPersistentEditor(item)
        self.editItem(item)
        self.isEdit = True
        self.index = index

    # 关闭编辑
    def close_edit(self, *_) -> None:
        if self.edited_item:
            self.isEdit = False
            self.closePersistentEditor(self.edited_item)
            print(self.curNode.children)
            while True:
                sameName = False
                for i in range(len(self.curNode.children) - 1):
                    if self.edited_item.text() == self.curNode.children[i].name and self.index != i:
                        self.edited_item.setText(self.edited_item.text() + "(2)")
                        sameName = True
                        print('same name')
                        break
                if not sameName:
                    break

            # 更新节点名称
            self.curNode.children[self.index].name = self.edited_item.text()
            
            # 确保重命名后字体大小与当前视图一致
            if hasattr(self.parents, 'fontSizes') and hasattr(self.parents, 'currentIconSize'):
                current_font = QFont("Times New Roman", self.parents.fontSizes[self.parents.currentIconSize])
                self.edited_item.setFont(current_font)
                
            self.parents.updateTree()
            self.edited_item = None

# 自定义悬浮框类
class CustomTooltip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)
        
        # 创建内容容器 - 这个容器将设置背景色
        self.container = QFrame(self)
        self.container.setObjectName("tooltipContainer")
        self.container.setStyleSheet("""
            #tooltipContainer {
                background-color:rgba(80, 80, 80, 0.59);
                border-radius: 4px;
                border: 1px solid rgba(80, 80, 80, 0.59);
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 创建文本标签
        self.text_label = QLabel(self.container)
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-family: "Times New Roman", Times, serif;
                background-color: transparent;
                font-size: 10pt;
            }
        """)
        self.container_layout.addWidget(self.text_label)
        
        # 将容器添加到主布局
        self.layout.addWidget(self.container)
        
        # 初始化不可见
        self.hide()
    
    # 重写绘制事件
    def paintEvent(self, event):
        # 确保背景透明
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.transparent)
        super().paintEvent(event)
        
    def showTooltip(self, content, pos):
        # 设置内容
        self.text_label.setText(content)
        
        # 调整大小
        self.adjustSize()
        
        # 计算位置
        screen_rect = QApplication.desktop().screenGeometry()
        tooltip_width = self.width()
        tooltip_height = self.height()
        
        # 确保工具提示不会超出屏幕
        x = min(pos.x() + 15, screen_rect.width() - tooltip_width - 5)
        y = min(pos.y(), screen_rect.height() - tooltip_height - 5)
        
        # 设置位置
        self.move(x, y)
        
        # 显示并提升到最上层
        self.show()
        self.raise_()
        
    def hideTooltip(self):
        self.hide()
