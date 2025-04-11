import os
import sys
import time
import pickle
from typing import Optional

import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

BLOCKSIZE = 512     # 每个物理块的大小
BLOCKNUMBER = 512   # 在磁盘中物理块的个数

# 定义类：磁盘中的物理块
class Block:
    def __init__(self, blockIndex: int, data = ""):
        self.blockIndex = blockIndex            # 物理块的编号
        self.data = data                        # 物理块中的数据

    def read(self):                             # 读取物理块中的数据
        return self.data

    def write(self, newData: str):              # 将数据写入物理块
        self.data = newData[:BLOCKSIZE]
        return newData[BLOCKSIZE:]

    def append(self, newData:str) -> str:       # 在物理块中新增内容
        remainSpace = BLOCKSIZE - len(self.data)
        # 如果剩余空间足够
        if remainSpace >= newData:
            return ""
        # 如果剩余空间不足
        else:
            self.data += newData[:remainSpace]
            return newData[remainSpace:]

    def isFull(self):                           # 判断物理块是否满
        return len(self.data) == BLOCKSIZE

    def clear(self):                            # 清空物理块中的数据
        self.data = ""

# 定义类：FAT(文件分配表)
class FAT:
    def __init__(self):
        self.fat = []
        for i in range(BLOCKNUMBER):
            self.fat.append(-2)                 # 初始化，所有空闲位置设为-2

    def findBlank(self):                        # 找到FAT表中一个空闲位置
        for i in range(BLOCKNUMBER):
            if self.fat[i] == -2:
                return i
        return -1
        
    # 计算所需的物理块数
    def calculateRequiredBlocks(self, data_size):
        # 计算需要多少个完整块
        full_blocks = data_size // BLOCKSIZE
        # 如果有剩余数据，还需要一个额外的块
        if data_size % BLOCKSIZE > 0:
            full_blocks += 1
        return full_blocks
        
    # 检查是否有足够的空闲块
    def hasEnoughSpace(self, data_size):
        required_blocks = self.calculateRequiredBlocks(data_size)
        free_blocks = 0
        
        # 计算FAT中的空闲块数量
        for i in range(BLOCKNUMBER):
            if self.fat[i] == -2:
                free_blocks += 1
                if free_blocks >= required_blocks:
                    return True
        
        return False

    def write(self, data, disk):                # 将数据写入磁盘
        start = -1
        current = -1

        while data != "":
            location = self.findBlank()
            if location == -1:                  # 找不到空闲位置了
                return -1  # 返回-1表示写入失败
            if current != -1:
                self.fat[current] = location
            else:
                start = location
            current = location
            data = disk[current].write(data)
            self.fat[current] = -1
        return start

    def delete(self, start, disk):              # 删除从start位置开始的所有数据
        if start == -1:
            return

        while self.fat[start] != -1:            # 同时也要更新FAT表
            disk[start].clear()
            first = self.fat[start]
            self.fat[start] = -2
            start = first

        self.fat[start] = -2
        disk[start].clear()

    def update(self, start, data, disk):        # 更新从start位置开始的所有数据
        # 计算新数据所需的块数
        required_blocks = self.calculateRequiredBlocks(len(data))
        
        # 计算当前占用的块数
        occupied_blocks = 0
        if start != -1:
            current = start
            while self.fat[current] != -1:
                occupied_blocks += 1
                current = self.fat[current]
            occupied_blocks += 1  # 加上最后一个块
        
        # 计算实际需要的额外空闲块数
        extra_blocks_needed = required_blocks - occupied_blocks
        
        # 如果需要额外块，检查是否有足够的空闲块
        if extra_blocks_needed > 0:
            free_blocks = 0
            for i in range(BLOCKNUMBER):
                if self.fat[i] == -2:
                    free_blocks += 1
                    if free_blocks >= extra_blocks_needed:
                        break
            
            # 如果空闲块不足，直接返回失败
            if free_blocks < extra_blocks_needed:
                return -1

        # 如果有足够空间或不需要额外空间，则安全删除原数据并写入新数据
        old_start = start  # 保存原起始位置，以防写入失败
        self.delete(start, disk) 
        new_start = self.write(data, disk)
        
        # 如果写入失败，尝试恢复原数据（虽然这种情况理论上不应该发生）
        if new_start == -1:
            # 这里可以添加恢复原数据的逻辑，但实际上前面的检查应该已经避免了这种情况
            pass
            
        return new_start

    def read(self, start, disk):                # 读取从start位置开始的所有数据
        data = ""
        while self.fat[start] != -1:
            data += disk[start].read()
            start = self.fat[start]
        data += disk[start].read()
        return data

# 定义类FCB(用于管理文件的原数据和文件操作)
class FCB:
    def __init__(self, name, createTime, data, fat, disk):
        self.name = name 
        self.createTime = createTime 
        self.updateTime = self.createTime 
        self.start = -1 

    def update(self, newData, fat, disk):       # 更新FCB
        new_start = fat.update(self.start, newData, disk)
        if new_start != -1:  # 检查更新是否成功
            self.start = new_start
            self.updateTime = time.localtime(time.time())
            return True
        return False

    def delete(self, fat, disk):                # 删除FCB
        fat.delete(self.start, disk) 

    def read(self, fat, disk):                  # 读取FCB中的内容
        if self.start == -1:
            return ""
        else:
            return fat.read(self.start, disk) 

# 定义类多目录节点
class CatalogNode: 
    def __init__(self, name, isFile, fat, disk, createTime, parent = None, data = ""):
        self.name = name                        # 名称
        self.isFile = isFile                    # 判断是否为文件
        self.parent = parent                    # 父节点
        self.createTime = createTime            # 创建时间
        self.updateTime = self.createTime       # 更新时间

        if not self.isFile: 
            self.children = []
        else: 
            self.data = FCB(name, createTime, data, fat, disk)

# 定义类：属性视图
class attributeForm(QWidget): 
    def __init__(self, name, isFile, createTime, updateTime, size, child = 0):
        super().__init__()

        # 设置提示框信息
        self.name = name
        self.setWindowTitle('attribute')
        self.setWindowIcon(QIcon('images/attribute.png'))
        self.resize(350, 220)  # 增加一点高度以适应新增内容
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

        # 文件更新时间1
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

# 定义类：文件系统主界面
class myWindow(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.readFile() 

        self.curNode = self.catalog[0] 
        self.rootNode = self.curNode
        self.baseUrl = ['root']
        
        # 添加剪贴板功能
        self.clipboard = None
        
        # 设置默认图标大小 (中图标)
        self.currentIconSize = 1  # 0=小图标, 1=中图标, 2=大图标
        # 定义三种大小：图标大小，网格大小，字体大小
        self.iconSizes = [(32, 32), (64, 64), (128, 128)]
        self.gridSizes = [(80, 70), (120, 100), (180, 150)]
        self.fontSizes = [8, 10, 12]  # 字体大小

        self.resize(1500,1000)
        self.setFont(QFont("Times New Roman", 10))
        self.setWindowTitle('fileSystem_by_2253744_林觉凯')
        self.setWindowIcon(QIcon('images/folder.ico'))

        qr = self.frameGeometry() 
        centerPlace = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(centerPlace)
        self.move(qr.topLeft())

        grid = QGridLayout() 
        grid.setSpacing(10)
        self.widGet = QWidget()
        self.widGet.setLayout(grid)
        self.setCentralWidget(self.widGet)

        # 格式化按键
        menubar = self.menuBar() 
        menubar.addAction('format ', self.format)
        menubar.setFont(QFont("Times New Roman", 10))

        # 返回键和前进键
        self.backAction = QAction(QIcon('images/back.png'), '&返回',self) # 返回键
        self.backAction.triggered.connect(self.backEvent)
        self.toolBar = self.addToolBar('工具栏')
        self.toolBar.addAction(self.backAction)
        self.backAction.setEnabled(False)
        self.forwardAction = QAction(QIcon('images/forward.png'), '&前进',self) # 前进键
        self.forwardAction.triggered.connect(self.forwardEvent)
        self.toolBar.addAction(self.forwardAction)
        self.forwardAction.setEnabled(False)
        self.toolBar.addSeparator()

        # 上方窗口路径显示
        self.curLocation = QLineEdit() 
        self.curLocation.setText('> root')
        self.curLocation.setReadOnly(True)
        font = QFont("Times New Roman", 12)
        self.curLocation.setFont(font)
        self.curLocation.addAction(QIcon('images/computer.png'), QLineEdit.LeadingPosition) 
        self.curLocation.setMinimumHeight(40)
        ptrLayout = QFormLayout()
        ptrLayout.addRow(self.curLocation)
        ptrWidget = QWidget()
        ptrWidget.setLayout(ptrLayout)
        ptrWidget.adjustSize()
        self.toolBar.addWidget(ptrWidget) 
        self.toolBar.setMovable(False)
        
        # 添加搜索框，添加按回车提示
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("Search... (press enter to display)")
        self.searchBox.setFont(QFont("Times New Roman", 10))
        self.searchBox.setClearButtonEnabled(True)
        self.searchBox.addAction(QIcon('images/search.png'), QLineEdit.LeadingPosition)
        self.searchBox.returnPressed.connect(self.searchFiles)
        searchLayout = QFormLayout()
        searchLayout.addRow(self.searchBox)
        searchWidget = QWidget()
        searchWidget.setLayout(searchLayout)
        searchWidget.setMaximumWidth(400)
        self.toolBar.addWidget(searchWidget)

        # 左边窗口目录显示
        self.tree = QTreeWidget()
        self.setFont(QFont("Times New Roman", 11))
        self.tree.setColumnCount(1) 
        self.tree.setHeaderLabels(['Path address']) 
        self.buildTree() 
        self.tree.setCurrentItem(self.rootItem) 
        self.treeItem = [self.rootItem] 
        self.tree.itemClicked['QTreeWidgetItem*','int'].connect(self.clickTreeItem) # 绑定单击事件
        grid.addWidget(self.tree, 1, 0)

        self.listView = File_Widget(self.curNode, parents=self)
        self.listView.setFont(QFont("Times New Roman", 11))
        self.listView.setMinimumWidth(1000)
        self.listView.setViewMode(QListView.IconMode)
        # 使用当前图标大小
        self.updateIconSize()
        self.listView.setResizeMode(QListView.Adjust)
        self.listView.setMovement(QListView.Static)
        self.listView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.listView.doubleClicked.connect(self.openFile)

        self.loadCurFile()
        grid.addWidget(self.listView, 1, 1)
        self.listView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.show_menu)

        # 初始化状态栏
        self.initStatusBar()
        
        self.updatePrint()
        self.lastLoc = -1
        
        # 添加快捷键
        QShortcut(QKeySequence(self.tr("Delete")), self, self.deleteFile)
        QShortcut(QKeySequence(self.tr("Ctrl+C")), self, self.copyFile)
        QShortcut(QKeySequence(self.tr("Ctrl+V")), self, self.pasteFile)
        QShortcut(QKeySequence(self.tr("F2")), self, self.rename)
        QShortcut(QKeySequence(self.tr("Ctrl+F")), self, self.focusSearch)

    # 初始化状态栏
    def initStatusBar(self):
        self.statusBar = self.statusBar()
        
        # 项目数量标签
        self.projectCountLabel = QLabel()
        self.projectCountLabel.setFont(QFont("Times New Roman", 10))
        self.statusBar.addWidget(self.projectCountLabel)
        
        # 添加固定宽度的空白区域
        spacer = QWidget()
        spacer.setFixedWidth(20)
        self.statusBar.addWidget(spacer)
        
        # 内存使用进度条
        self.memoryProgressBar = QProgressBar()
        self.memoryProgressBar.setFixedWidth(200)
        self.memoryProgressBar.setFixedHeight(16)
        self.memoryProgressBar.setTextVisible(False)  # 不显示进度条上的文字
        self.statusBar.addWidget(self.memoryProgressBar)
        
        # 内存使用文本信息
        self.memoryInfoLabel = QLabel()
        self.memoryInfoLabel.setFont(QFont("Times New Roman", 10))
        self.statusBar.addWidget(self.memoryInfoLabel)

    # 计算已使用内存
    def calculateUsedMemory(self):
        used_blocks = 0
        for i in range(BLOCKNUMBER):
            if self.fat.fat[i] != -2:  # -2表示空闲
                used_blocks += 1
        
        used_memory = used_blocks * BLOCKSIZE
        total_memory = BLOCKNUMBER * BLOCKSIZE
        
        return used_memory, total_memory

    # 更新上方窗口路径和状态栏
    def updatePrint(self):
        # 更新项目数量显示
        self.projectCountLabel.setText(str(len(self.curNode.children)) + ' project(s)')
        
        # 更新内存使用情况
        used_memory, total_memory = self.calculateUsedMemory()
        usage_percent = (used_memory / total_memory) * 100
        
        # 设置进度条
        self.memoryProgressBar.setValue(int(usage_percent))
        
        # 根据使用率改变进度条颜色
        if usage_percent < 60:
            # 绿色 - 内存充足
            color = "#4CAF50"
        elif usage_percent < 80:
            # 黄色 - 内存使用较多
            color = "#FFC107"
        else:
            # 红色 - 内存不足警告
            color = "#F44336"
            
        self.memoryProgressBar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
        # 格式化内存显示为精确的字节数
        # 使用更通用的方式实现千位分隔符
        def format_bytes(num):
            result = ''
            num_str = str(num)
            while len(num_str) > 3:
                result = ',' + num_str[-3:] + result
                num_str = num_str[:-3]
            result = num_str + result
            return result
            
        used_bytes_formatted = format_bytes(used_memory)
        total_bytes_formatted = format_bytes(total_memory)
        memory_text = f"{used_bytes_formatted} bytes / {total_bytes_formatted} bytes ({usage_percent:.1f}%)"
        
        self.memoryInfoLabel.setText(memory_text)
        
        # 更新路径显示
        s ='> root'
        for i,item in enumerate(self.baseUrl):
            if i == 0:
                continue
            s += " > " + item
        self.curLocation.setText(s)

    def clickTreeItem(self,item,column): 
        ways = [item]
        level = 0 
        temp = item

        while temp.parent() != None:
            temp = temp.parent()
            ways.append(temp)
            level += 1
        ways.reverse()
        while self.backEvent(): 
            pass
        self.baseUrl = self.baseUrl[:1]
        self.treeItem = self.treeItem[:1]

        for i in ways: 
            if i == self.rootItem:
                continue

            newNode = None
            for j in self.curNode.children:
                if j.name == i.text(0):
                    newNode = j
                    break
            if newNode.isFile:
                break
            else:
                self.curNode = newNode
                self.updateLoc()
                self.baseUrl.append(newNode.name)

                for j in range(self.treeItem[-1].childCount()):
                    if self.treeItem[-1].child(j).text(0) == newNode.name:
                        selectedItem = self.treeItem[-1].child(j)
                self.treeItem.append(selectedItem)
                self.tree.setCurrentItem(selectedItem)

        self.updatePrint()
        if self.curNode != self.rootNode:
            self.backAction.setEnabled(True)
        self.forwardAction.setEnabled(False)
        self.lastLoc = -1

    # 更新位置
    def updateLoc(self):
        self.loadCurFile()
        self.listView.curNode = self.curNode

    # 打开文件
    def openFile(self,modelindex: QModelIndex) -> None: 
        self.listView.close_edit() 
        
        # 重置悬浮状态，防止引用已删除对象
        if hasattr(self.listView, 'resetHoverState'):
            self.listView.resetHoverState()
            
        try:
            item = self.listView.item(modelindex.row())
        except:
            if len(self.listView.selectedItems()) == 0:
                return
            item = self.listView.selectedItems()[-1]

        if self.lastLoc != -1 and self.nextStep:  
            item = self.listView.item(self.lastLoc)
            self.lastLoc = -1
            self.forwardAction.setEnabled(False)
        self.nextStep = False

        newNode = None
        for i in self.curNode.children:
            if i.name == item.text():
                newNode = i
                break

        if newNode.isFile:
            data = newNode.data.read(self.fat,self.disk)
            self.child = editForm(newNode.name, data)
            self.child._signal.connect(self.getData)
            self.child.show()
            self.writeFile = newNode
        else:
            self.listView.close_edit()
            self.curNode = newNode
            self.updateLoc()
            self.baseUrl.append(newNode.name)

            for i in range(self.treeItem[-1].childCount()): 
                if self.treeItem[-1].child(i).text(0) == newNode.name:
                    selectedItem = self.treeItem[-1].child(i)
            self.treeItem.append(selectedItem)
            self.tree.setCurrentItem(selectedItem)
            self.backAction.setEnabled(True)
            self.updatePrint()

    # 重命名操作
    def rename(self):
        if len(self.listView.selectedItems()) == 0:
            return
        self.listView.editSelected(self.listView.selectedIndexes()[-1].row()) 
        self.updateTree()

    # 删除操作
    def deleteFile(self): 
        if len(self.listView.selectedItems()) == 0:
            return

        item = self.listView.selectedItems()[-1]
        index = self.listView.selectedIndexes()[-1].row()
        reply = QMessageBox() 
        reply.setFont(QFont("Times New Roman", 10))
        reply.setWindowTitle('warning')
        reply.setWindowIcon(QIcon('images/warning.png'))
        if self.curNode.children[index].isFile: 
            reply.setText('whether to delete the file"' + item.text() + '"?   ')
        else:
            reply.setText('whether to delete the folder"' + item.text() + '"? ')
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        buttonY = reply.button(QMessageBox.Yes)
        buttonY.setText('yes')
        buttonN = reply.button(QMessageBox.No)
        buttonN.setText('cancel')
        reply.exec_()
        if reply.clickedButton() == buttonN:
            return
        self.listView.takeItem(index) 
        del item
        self.deleteFileRecursive(self.curNode.children[index]) 
        self.curNode.children.remove(self.curNode.children[index])
        self.catalog = self.updateCatalog(self.rootNode) 
        self.updateTree() 
        # 更新内存使用情况显示
        self.updatePrint()

    # 递归删除
    def deleteFileRecursive(self,node): 
        if node.isFile:
            node.data.delete(self.fat,self.disk)
        else:
            for i in node.children:
                self.deleteFileRecursive(i)

    # 更新多目录节点
    def updateCatalog(self,node): 
        if node.isFile:
            return [node]
        else:
            element = [node]
            for i in node.children:
                element += self.updateCatalog(i)
            return element

    # 新建文件夹
    def createFolder(self):
        # 使用当前设置的字体大小
        current_font = QFont("Times New Roman", self.fontSizes[self.currentIconSize])
        
        # 获取唯一的文件夹名称
        folderName = self.getUniqueNameInFolder("New Folder", self.curNode)
        
        self.item_1 = QListWidgetItem(QIcon("images/folder.png"), folderName)
        self.item_1.setFont(current_font)  # 应用当前字体大小
        self.listView.addItem(self.item_1)
        self.listView.editLast()
        newNode = CatalogNode(self.item_1.text(),False,self.fat,self.disk,time.localtime(time.time()),self.curNode)
        self.curNode.children.append(newNode)
        self.catalog.append(newNode)
        self.updateTree()
        # 更新内存使用情况显示
        self.updatePrint()

    # 新建文件
    def createFile(self):
        # 检查是否至少有一个空闲块可用
        if self.fat.findBlank() == -1:
            self.showDiskFullWarning()
            return
        
        # 使用当前设置的字体大小
        current_font = QFont("Times New Roman", self.fontSizes[self.currentIconSize])
        
        # 获取唯一的文件名称    
        fileName = self.getUniqueNameInFolder("New File", self.curNode)
            
        self.item_1 = QListWidgetItem(QIcon("images/file.png"), fileName)
        self.item_1.setFont(current_font)  # 应用当前字体大小
        self.listView.addItem(self.item_1)
        self.listView.editLast()
        newNode = CatalogNode(self.item_1.text(),True,self.fat,self.disk,time.localtime(time.time()),self.curNode)
        self.curNode.children.append(newNode)
        self.catalog.append(newNode)
        self.updateTree()
        # 更新内存使用情况显示
        self.updatePrint()

    # 计算文件或文件夹的大小
    def getSize(self, node):
        if node.isFile:
            # 文件大小就是其内容的字节长度
            data = node.data.read(self.fat, self.disk)
            return len(data)
        else:
            # 文件夹大小是其所有子文件的大小总和
            total_size = 0
            for child in node.children:
                total_size += self.getSize(child)
            return total_size

    # 属性视图
    def viewAttribute(self): 
        if len(self.listView.selectedItems()) == 0:
            # 当前目录的属性
            size = self.getSize(self.curNode)
            self.child = attributeForm(self.curNode.name, False, self.curNode.createTime, self.curNode.updateTime, size, len(self.curNode.children))
            self.child.show()
            return
        else:
            node = self.curNode.children[self.listView.selectedIndexes()[-1].row()]
            size = self.getSize(node)
            if node.isFile:
                self.child = attributeForm(node.name, node.isFile, node.createTime, node.updateTime, size, 0)
            else:
                self.child = attributeForm(node.name, node.isFile, node.createTime, node.updateTime, size, len(node.children))
            self.child.show()
            return

    # 右击显示菜单
    def show_menu(self, point):
        menu = QMenu(self.listView)
        menu.setFont(QFont("Times New Roman", 10))

        if len(self.listView.selectedItems()) != 0:
            # 获取当前选中的项目
            index = self.listView.selectedIndexes()[-1].row()
            selectedNode = self.curNode.children[index]
            
            openFileAction = QAction(QIcon('images/open.png'), '    open')   # 打开
            openFileAction.triggered.connect(self.openFile)
            menu.addAction(openFileAction)

            # 为文件和文件夹都添加复制选项
            copyAction = QAction(QIcon('images/copy.png'), '    copy')   # 复制
            copyAction.triggered.connect(self.copyFile)
            menu.addAction(copyAction)

            renameAction = QAction(QIcon('images/rename.png'), '    rename') # 重命名
            renameAction.triggered.connect(self.rename)
            menu.addAction(renameAction)

            deleteAction = QAction(QIcon('images/delete.png'), '    delete') # 删除
            deleteAction.triggered.connect(self.deleteFile)
            menu.addAction(deleteAction)

            viewAttributeAction = QAction(QIcon('images/attribute.png'), '    attribute')    # 属性
            viewAttributeAction.triggered.connect(self.viewAttribute)
            menu.addAction(viewAttributeAction)

            dest_point = self.listView.mapToGlobal(point)
            menu.exec_(dest_point)

        else:
            # 空白区域右键菜单
            # 添加"查看"子菜单
            viewMenu = QMenu(menu)
            viewMenu.setTitle('view')
            viewMenu.setFont(QFont("Times New Roman", 10))
            
            smallIconAction = QAction(QIcon('images/small.png') if os.path.exists('images/small.png') else QIcon(), '  small icons')
            smallIconAction.triggered.connect(self.setSmallIcons)
            viewMenu.addAction(smallIconAction)
            
            mediumIconAction = QAction(QIcon('images/middle.png') if os.path.exists('images/middle.png') else QIcon(), '  medium icons')
            mediumIconAction.triggered.connect(self.setMediumIcons)
            viewMenu.addAction(mediumIconAction)
            
            largeIconAction = QAction(QIcon('images/big.png') if os.path.exists('images/big.png') else QIcon(), '  large icons')
            largeIconAction.triggered.connect(self.setLargeIcons)
            viewMenu.addAction(largeIconAction)
            
            # 设置图标，如果see.png存在就使用它
            viewMenu.setIcon(QIcon('images/see.png') if os.path.exists('images/see.png') else QIcon())
            menu.addMenu(viewMenu)
            
            # 原有的"新建"菜单
            createMenu = QMenu(menu)
            createMenu.setTitle('new')
            createMenu.setFont(QFont("Times New Roman", 10))
            createFolderAction = QAction(QIcon('images/folder.png'), '  folder') 
            createFolderAction.triggered.connect(self.createFolder)
            createMenu.addAction(createFolderAction)
            createFileAction = QAction(QIcon('images/file.png'), '  file')
            createFileAction.triggered.connect(self.createFile)
            createMenu.addAction(createFileAction)
            createMenu.setIcon(QIcon('images/create.png'))
            menu.addMenu(createMenu)
            
            # 添加粘贴选项（仅当剪贴板有内容时）
            if self.clipboard:
                pasteAction = QAction(QIcon('images/paste.png'), 'paste')   # 粘贴
                pasteAction.triggered.connect(self.pasteFile)
                menu.addAction(pasteAction)
                
            viewAttributeAction = QAction(QIcon('images/attribute.png'), 'attribute')
            viewAttributeAction.triggered.connect(self.viewAttribute)
            menu.addAction(viewAttributeAction)
            self.nextStep = False
            dest_point = self.listView.mapToGlobal(point)
            menu.exec_(dest_point)

    # 更新结点树
    def updateTree(self):
        node = self.rootNode
        item = self.rootItem
        if item.childCount() < len(node.children):
            # 增加缺少的子项目
            for i in range(item.childCount(), len(node.children)):
                QTreeWidgetItem(item)
        elif item.childCount() > len(node.children):
            # 移除多余的子项目
            for i in range(item.childCount() - 1, len(node.children) - 1, -1):
                item.removeChild(item.child(i))

        # 更新所有子节点
        for i in range(len(node.children)):
            if i < item.childCount():  # 确保索引有效
                child_item = item.child(i)
                if child_item:  # 确保子项不为None
                    self.updateTreeRecursive(node.children[i], child_item)
        
        # 最后更新根节点本身
        self.updateTreeRecursive(node, item)

    def updateTreeRecursive(self, node : CatalogNode, item : QTreeWidgetItem): 
        # 安全检查：确保item不为None
        if item is None:
            return
            
        item.setText(0, node.name)
        if node.isFile:
            item.setIcon(0, QIcon('images/file.png'))
        else:
            if len(node.children) == 0:
                item.setIcon(0, QIcon('images/folder.png'))
            else:
                item.setIcon(0, QIcon('images/folder.png'))
                
            # 调整子项数量
            current_child_count = item.childCount()
            
            # 如果需要更多子项，创建它们
            if current_child_count < len(node.children):
                for i in range(current_child_count, len(node.children)):
                    QTreeWidgetItem(item)
            
            # 如果有多余的子项，移除它们
            elif current_child_count > len(node.children):
                for i in range(current_child_count - 1, len(node.children) - 1, -1):
                    item.removeChild(item.child(i))
            
            # 更新所有子节点
            for i in range(len(node.children)):
                if i < item.childCount():  # 确保索引有效
                    child_item = item.child(i)
                    if child_item:  # 确保子项不为None
                        self.updateTreeRecursive(node.children[i], child_item)

    # 建立树
    def buildTree(self): 
        self.tree.clear()
        self.rootItem = self.buildTreeRecursive(self.catalog[0],self.tree)
        self.tree.addTopLevelItem(self.rootItem)
        self.tree.expandAll()

    # 获取数据
    def getData(self, parameter): 
        # 不再需要额外的空间检查，因为FCB.update方法中已经包含了更精确的空间检查
        # 尝试更新文件数据
        success = self.writeFile.data.update(parameter, self.fat, self.disk)
        if not success:
            self.showDiskFullWarning()
            return
            
        self.writeFile.updateTime = time.localtime(time.time())
        # 更新内存使用情况显示
        self.updatePrint()

    # 递归构建树
    def buildTreeRecursive(self,node: CatalogNode,parent: QTreeWidgetItem): 
        child = QTreeWidgetItem(parent)
        child.setText(0,node.name)

        if node.isFile:
            child.setIcon(0, QIcon('images/file.png'))
        else:
            if len(node.children) == 0:
                child.setIcon(0, QIcon('images/folder.png'))
            else:
                child.setIcon(0, QIcon('images/folder.png'))
            for i in node.children:
                self.buildTreeRecursive(i, child)
        return child

    def loadCurFile(self): 
        # 重置悬浮状态，防止引用已删除对象
        if hasattr(self.listView, 'resetHoverState'):
            self.listView.resetHoverState()
            
        self.listView.clear()

        # 当前字体大小
        current_font = QFont("Times New Roman", self.fontSizes[self.currentIconSize])

        for i in self.curNode.children:
            if i.isFile:
                self.item_1 = QListWidgetItem(QIcon("images/file.png"), i.name)
                self.item_1.setFont(current_font)  # 设置字体大小
                self.listView.addItem(self.item_1)
            else:
                if len(i.children) == 0:
                    self.item_1 = QListWidgetItem(QIcon("images/folder.png"), i.name)
                else:
                    self.item_1 = QListWidgetItem(QIcon("images/folder.png"), i.name)
                self.item_1.setFont(current_font)  # 设置字体大小
                self.listView.addItem(self.item_1)

    # 格式化操作
    def format(self): 
        self.listView.close_edit()
        reply = QMessageBox()
        reply.setFont(QFont("Times New Roman", 10))
        reply.setWindowTitle('warning')
        reply.setWindowIcon(QIcon('images/warning.png'))
        reply.setText('whether to format the disk?')
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        buttonY = reply.button(QMessageBox.Yes)
        buttonY.setText('yes')
        buttonN = reply.button(QMessageBox.No)
        buttonN.setText('cancel')
        reply.exec_()
        reply.show()
        if reply.clickedButton() == buttonN:
            return

        self.fat = FAT()
        self.fat.fat = [-2] * BLOCKNUMBER
        with open('fat','wb') as f:
            f.write(pickle.dumps(self.fat))

        self.disk = []
        for i in range(BLOCKNUMBER):
            self.disk.append(Block(i))
        with open('disk','wb') as f:
            f.write(pickle.dumps(self.disk))

        self.catalog = []
        self.catalog.append(CatalogNode("root", False, self.fat, self.disk, time.localtime(time.time())))
        with open('catalog','wb') as f:
            f.write(pickle.dumps(self.catalog))
        self.hide()
        self.winform = myWindow()
        self.winform.show()

    # 保存文件
    def saveFile(self): 
        with open('fat','wb') as f:
            f.write(pickle.dumps(self.fat))
        with open('disk','wb') as f:
            f.write(pickle.dumps(self.disk))
        with open('catalog','wb') as f:
            f.write(pickle.dumps(self.catalog))

    # 读取文件
    def readFile(self): 
        if not os.path.exists('fat'):
            self.fat = FAT()
            self.fat.fat = [-2] * BLOCKNUMBER
            with open('fat','wb') as f:
                f.write(pickle.dumps(self.fat))
        else:
            with open('fat','rb') as f:
                self.fat = pickle.load(f)

        if not os.path.exists('disk'):
            self.disk = []
            for i in range(BLOCKNUMBER):
                self.disk.append(Block(i))
            with open('disk','wb') as f:
                f.write(pickle.dumps(self.disk))
        else:
            with open('disk','rb') as f:
                self.disk = pickle.load(f)

        if not os.path.exists('catalog'):
            self.catalog = []
            self.catalog.append(CatalogNode("root", False, self.fat, self.disk, time.localtime(time.time())))
            with open('catalog','wb') as f:
                f.write(pickle.dumps(self.catalog))
        else:
            with open('catalog','rb') as f:
                self.catalog = pickle.load(f)

    # 初始化
    def initial(self):
        self.fat = FAT()
        self.fat.fat = [-2] * BLOCKNUMBER
        with open('fat','ab') as f:
            f.write(pickle.dumps(self.fat))
        self.disk = []
        for i in range(BLOCKNUMBER):
            self.disk.append(Block(i))
        with open('disk','ab') as f:
            f.write(pickle.dumps(self.disk))
        self.catalog = []
        self.catalog.append(CatalogNode("root", False, self.fat, self.disk, time.localtime(time.time())))
        with open('catalog','ab') as f:
            f.write(pickle.dumps(self.catalog))

    # 返回
    def backEvent(self): 
        self.listView.close_edit()

        if self.rootNode == self.curNode: 
            return False
        for i in range(len(self.curNode.parent.children)):
            if self.curNode.parent.children[i].name == self.curNode.name:
                self.lastLoc = i
                self.forwardAction.setEnabled(True)
                break

        self.curNode = self.curNode.parent
        self.updateLoc()
        self.baseUrl.pop()
        self.treeItem.pop()
        self.tree.setCurrentItem(self.treeItem[-1])
        self.updateTree()
        self.updatePrint()
        if self.curNode == self.rootNode:
            self.backAction.setEnabled(False)
        return True

    # 前进
    def forwardEvent(self): 
        self.nextStep = True
        self.openFile(QModelIndex())

    def closeEvent(self, event): 
        self.listView.close_edit()
        reply = QMessageBox()
        reply.setFont(QFont("Times New Roman", 10))
        reply.setWindowTitle('warning')
        reply.setWindowIcon(QIcon("images/disk.png"))
        reply.setText('Write this operation to the disk?')
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Ignore)
        buttonY = reply.button(QMessageBox.Yes)
        buttonY.setText('yes')
        buttonI = reply.button(QMessageBox.Ignore)
        buttonI.setText('no')
        buttonN = reply.button(QMessageBox.No)
        buttonN.setText('cancel')
        reply.exec_()

        if reply.clickedButton() == buttonI:
            event.accept()
        elif reply.clickedButton() == buttonY:
            self.saveFile()
            event.accept()
        else:
            event.ignore()

    # 修改复制功能方法，允许复制文件夹
    def copyFile(self):
        if len(self.listView.selectedItems()) == 0:
            return
        
        index = self.listView.selectedIndexes()[-1].row()
        node = self.curNode.children[index]
        
        # 存储被复制的节点
        self.clipboard = node
        
        # 修改为与其他提示框统一的风格
        reply = QMessageBox()
        reply.setFont(QFont("Times New Roman", 10))
        reply.setWindowTitle('information')
        reply.setWindowIcon(QIcon('images/copy.png'))
        if node.isFile:
            reply.setText(f'File "{self.clipboard.name}" has been copied.')
        else:
            reply.setText(f'Folder "{self.clipboard.name}" has been copied.')
        reply.setStandardButtons(QMessageBox.Ok)
        buttonOk = reply.button(QMessageBox.Ok)
        buttonOk.setText('ok')
        reply.exec_()

    # 粘贴功能
    def pasteFile(self):
        if not self.clipboard:
            return
        
        # 获取唯一名称
        targetName = self.getUniqueNameInFolder(self.clipboard.name, self.curNode)
        
        # 检查是否有足够空间
        if self.clipboard.isFile:
            # 文件复制
            data_size = len(self.clipboard.data.read(self.fat, self.disk))
            if not self.fat.hasEnoughSpace(data_size):
                self.showDiskFullWarning()
                return
            
            # 复制文件节点
            self.pasteFileNode(self.clipboard, targetName, self.curNode)
        else:
            # 文件夹复制 - 先检查总大小
            folder_size = self.calculateFolderSize(self.clipboard)
            if not self.fat.hasEnoughSpace(folder_size):
                self.showDiskFullWarning()
                return
            
            # 复制文件夹及其内容
            newNode = CatalogNode(targetName, False, self.fat, self.disk, time.localtime(time.time()), self.curNode)
            self.curNode.children.append(newNode)
            self.catalog.append(newNode)
            
            # 递归复制文件夹内容
            try:
                for child in self.clipboard.children:
                    self.copyFolderContents(child, newNode)
            except Exception as e:
                # 如果复制过程中发生错误，清理已复制的内容
                self.deleteFileRecursive(newNode)
                self.curNode.children.remove(newNode)
                self.catalog.remove(newNode)
                
                # 显示错误信息
                errorBox = QMessageBox()
                errorBox.setWindowTitle("Error")
                errorBox.setIcon(QMessageBox.Critical)
                errorBox.setText(f"Failed to copy folder: {str(e)}")
                errorBox.exec_()
                return
        
        # 刷新视图，确保使用正确的字体大小
        self.updateTree()
        self.loadCurFile()  # 这会应用当前的字体大小
        # 更新内存使用情况显示
        self.updatePrint()
    
    # 递归复制文件夹内容
    def copyFolderContents(self, sourceNode, targetParentNode):
        # 为当前节点创建一个唯一名称
        newName = self.getUniqueNameInFolder(sourceNode.name, targetParentNode)
        
        if sourceNode.isFile:
            # 复制文件
            if not self.pasteFileNode(sourceNode, newName, targetParentNode):
                raise Exception(f"Failed to copy file {sourceNode.name}")
        else:
            # 创建新文件夹节点
            newNode = CatalogNode(newName, False, self.fat, self.disk, time.localtime(time.time()), targetParentNode)
            targetParentNode.children.append(newNode)
            self.catalog.append(newNode)
            
            # 递归复制子内容
            for child in sourceNode.children:
                self.copyFolderContents(child, newNode)
                
    # 获取文件夹中的唯一名称
    def getUniqueNameInFolder(self, originalName, parentNode):
        # 检查是否已存在同名项
        existingNames = [child.name for child in parentNode.children]
        
        if originalName not in existingNames:
            return originalName
            
        # 检查是否已有编号后缀的同名项
        baseName = originalName
        maxNumber = 0
        
        # 使用正则表达式匹配"name(数字)"模式
        import re
        pattern = re.compile(r'^(.*?)(\(\d+\))$')
        
        # 首先检查原始名称是否已经有编号
        match = pattern.match(originalName)
        if match:
            baseName = match.group(1)  # 提取基本名称（不含编号）
        
        # 查找已存在的最大编号
        for name in existingNames:
            # 只检查与基本名称相关的项
            if name == baseName or name.startswith(baseName + "("):
                match = pattern.match(name)
                if match:
                    # 提取编号并更新最大值
                    numStr = match.group(2)[1:-1]  # 去掉括号
                    try:
                        num = int(numStr)
                        maxNumber = max(maxNumber, num)
                    except ValueError:
                        pass
        
        # 返回基本名称加下一个编号
        return f"{baseName}({maxNumber + 1})"

    # 计算文件夹所需空间
    def calculateFolderSize(self, folderNode):
        total_size = 0
        for child in folderNode.children:
            if child.isFile:
                data = child.data.read(self.fat, self.disk)
                total_size += len(data)
            else:
                total_size += self.calculateFolderSize(child)
        return total_size
        
    # 显示磁盘空间不足警告
    def showDiskFullWarning(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("警告")
        msgBox.setWindowIcon(QIcon('images/warning.png'))
        msgBox.setText("磁盘空间不足")
        msgBox.setInformativeText("无法完成操作，请先清理磁盘空间。")
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()
        
    # 搜索功能
    def focusSearch(self):
        self.searchBox.setFocus()

    def searchFiles(self):
        query = self.searchBox.text().strip().lower()
        if not query:
            return
        
        resultDialog = QDialog(self)
        resultDialog.setWindowTitle("Search Results")
        resultDialog.setWindowIcon(QIcon('images/search.png'))
        resultDialog.setWindowFlags(resultDialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        resultDialog.resize(800, 600)
        layout = QVBoxLayout()
        
        # 创建搜索结果列表
        resultList = QTreeWidget()
        resultList.setHeaderLabels(["Name", "Path", "Type"])
        resultList.setColumnWidth(0, 200)
        resultList.setColumnWidth(1, 350)
        resultList.setColumnWidth(2, 100)
        resultList.setFont(QFont("Times New Roman", 10))
        layout.addWidget(resultList)
        
        # 执行搜索
        results = self.searchRecursive(self.rootNode, query, "")
        
        # 显示结果
        if len(results) > 0:
            for result in results:
                name, path, isFile = result
                item = QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, path)
                item.setText(2, "File" if isFile else "Folder")
                
                # 设置图标
                if isFile:
                    item.setIcon(0, QIcon('images/file.png'))
                else:
                    item.setIcon(0, QIcon('images/folder.png'))
                
                resultList.addTopLevelItem(item)
        else:
            # 没有找到匹配项，显示提示信息
            noResultItem = QTreeWidgetItem()
            noResultItem.setText(0, "No matching files or folders found")
            font = QFont("Times New Roman", 10, QFont.StyleItalic)
            noResultItem.setFont(0, font)
            noResultItem.setForeground(0, QBrush(QColor(120, 120, 120)))
            noResultItem.setTextAlignment(0, Qt.AlignCenter)
            resultList.addTopLevelItem(noResultItem)
        
        if len(results) > 0:
            resultList.itemDoubleClicked.connect(lambda item: self.navigateToSearchResult(item.text(1)))
        
        # 添加按钮
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(resultDialog.accept)
        layout.addWidget(buttonBox)
        
        resultDialog.setLayout(layout)
        resultDialog.exec_()

    def searchRecursive(self, node, query, path):
        results = []
        currentPath = path + "/" + node.name if path else node.name
        
        # 检查当前节点是否匹配
        if query in node.name.lower():
            results.append((node.name, currentPath, node.isFile))
        
        # 如果是文件夹，递归搜索
        if not node.isFile:
            for child in node.children:
                results.extend(self.searchRecursive(child, query, currentPath))
        
        return results

    def navigateToSearchResult(self, path):
        # 解析路径
        parts = path.split("/")
        
        # 从根节点开始导航
        node = self.rootNode
        self.curNode = node
        self.baseUrl = ['root']
        self.treeItem = [self.rootItem]
        
        # 循环遍历路径各部分
        for i in range(1, len(parts)):
            found = False
            for child in node.children:
                if child.name == parts[i]:
                    node = child
                    found = True
                    
                    # 如果是文件夹，进入该文件夹
                    if not child.isFile and i < len(parts) - 1:
                        self.curNode = node
                        self.baseUrl.append(node.name)
                        
                        # 更新树视图
                        childFound = False
                        for j in range(self.treeItem[-1].childCount()):
                            childItem = self.treeItem[-1].child(j)
                            # 确保子节点存在且文本匹配
                            if childItem and childItem.text(0) == node.name:
                                self.treeItem.append(childItem)
                                childFound = True
                                break
                        
                        # 如果找不到子节点，则不继续搜索
                        if not childFound:
                            break
                    
                    break
            
            if not found:
                break
        
        # 更新UI
        if self.treeItem and len(self.treeItem) > 0:
            self.tree.setCurrentItem(self.treeItem[-1])
        self.updateLoc()
        self.updatePrint()
        
        # 如果最后一项是文件，打开它
        if node.isFile:
            # 查找对应的列表项并选中
            for i in range(self.listView.count()):
                if self.listView.item(i).text() == node.name:
                    self.listView.setCurrentItem(self.listView.item(i))
                    # 打开文件
                    data = node.data.read(self.fat, self.disk)
                    self.child = editForm(node.name, data)
                    self.child._signal.connect(self.getData)
                    self.child.show()
                    self.writeFile = node
                    break

    # 更新图标大小
    def updateIconSize(self):
        idx = self.currentIconSize
        # 设置图标大小
        self.listView.setIconSize(QSize(*self.iconSizes[idx]))
        # 设置网格大小
        self.listView.setGridSize(QSize(*self.gridSizes[idx]))
        
        # 更新所有项目的字体大小
        font = QFont("Times New Roman", self.fontSizes[idx])
        for i in range(self.listView.count()):
            item = self.listView.item(i)
            item.setFont(font)
        
        # 刷新视图以应用更改
        self.listView.reset()
        
    # 设置小图标
    def setSmallIcons(self):
        self.currentIconSize = 0
        # 重置悬浮状态，防止引用已删除对象
        if hasattr(self.listView, 'resetHoverState'):
            self.listView.resetHoverState()
        self.updateIconSize()
        self.loadCurFile()  # 重新加载当前文件以确保图标大小正确应用
        
    # 设置中图标
    def setMediumIcons(self):
        self.currentIconSize = 1
        # 重置悬浮状态，防止引用已删除对象
        if hasattr(self.listView, 'resetHoverState'):
            self.listView.resetHoverState()
        self.updateIconSize()
        self.loadCurFile()  # 重新加载当前文件以确保图标大小正确应用
        
    # 设置大图标
    def setLargeIcons(self):
        self.currentIconSize = 2
        # 重置悬浮状态，防止引用已删除对象
        if hasattr(self.listView, 'resetHoverState'):
            self.listView.resetHoverState()
        self.updateIconSize()
        self.loadCurFile()  # 重新加载当前文件以确保图标大小正确应用

    # 复制文件节点
    def pasteFileNode(self, sourceNode, targetName, parentNode):
        # 读取源文件内容
        data = sourceNode.data.read(self.fat, self.disk)
        
        # 创建新节点并写入数据
        newNode = CatalogNode(targetName, True, self.fat, self.disk, time.localtime(time.time()), parentNode)
        success = newNode.data.update(data, self.fat, self.disk)
        
        # 如果写入成功，添加到父节点和目录列表
        if success:
            parentNode.children.append(newNode)
            self.catalog.append(newNode)
            return True
        return False

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

# 主函数
if __name__=='__main__':
    app = QApplication(sys.argv)
    myWindow = myWindow()
    myWindow.show()
    sys.exit(app.exec_())