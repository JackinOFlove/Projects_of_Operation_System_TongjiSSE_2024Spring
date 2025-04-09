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

    def write(self, data, disk):                # 将数据写入磁盘
        start = -1
        current = -1

        while data != "":
            location = self.findBlank()
            if location == -1:                  # 找不到空闲位置了
                raise Exception(print('磁盘空间不足'))
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
        self.delete(start, disk) 
        return self.write(data, disk) 

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
        self.start = fat.update(self.start, newData, disk) 

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
    def __init__(self, name, isFile, createTime, updateTime, child = 0):
        super().__init__()

        # 设置提示框信息
        self.name = name
        self.setWindowTitle('attribute')
        self.setWindowIcon(QIcon('images/attribute.png'))
        self.resize(350, 200)
        layout = QVBoxLayout()

        if isFile: 
            self.icon = QPixmap('images/file.png')
        else:
            self.icon = QPixmap('images/folder.png')

        fileType = QLabel(self)
        if isFile:
            fileType.setText('type: file')
        else:
            fileType.setText('type: folder')
        fileType.setFont(QFont('Times New Roman', 10))
        layout.addWidget(fileType)

        # 文件/文件夹名称
        fileName = QLabel(self)
        fileName.setText('name: ' + self.name)
        fileName.setFont(QFont('Times New Roman', 10))
        layout.addWidget(fileName)

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
        createLabel.setText('create time: ' + year + '.' + month + '.' + day + '. ' + hour + ':' + minute + ':' + second)
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

            self.curNode.children[self.index].name = self.edited_item.text()
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
        self.listView.setIconSize(QSize(100,100))
        self.listView.setGridSize(QSize(120,100))
        self.listView.setResizeMode(QListView.Adjust)
        self.listView.setMovement(QListView.Static)
        self.listView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.listView.doubleClicked.connect(self.openFile)

        self.loadCurFile()
        grid.addWidget(self.listView, 1, 1)
        self.listView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.show_menu)

        self.updatePrint()
        self.lastLoc = -1
        
        # 添加快捷键
        QShortcut(QKeySequence(self.tr("Delete")), self, self.deleteFile)
        QShortcut(QKeySequence(self.tr("Ctrl+C")), self, self.copyFile)
        QShortcut(QKeySequence(self.tr("Ctrl+V")), self, self.pasteFile)
        QShortcut(QKeySequence(self.tr("F2")), self, self.rename)
        QShortcut(QKeySequence(self.tr("Ctrl+F")), self, self.focusSearch)

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

    # 更新上方窗口路径
    def updatePrint(self):
        self.statusBar().showMessage(str(len(self.curNode.children)) + ' project(s)')
        s ='> root'
        for i,item in enumerate(self.baseUrl):
            if i == 0:
                continue
            s += " > " + item
        self.curLocation.setText(s)

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
        self.item_1 = QListWidgetItem(QIcon("images/folder.png"), "新建文件夹")
        self.listView.addItem(self.item_1)
        self.listView.editLast()
        newNode = CatalogNode(self.item_1.text(),False,self.fat,self.disk,time.localtime(time.time()),self.curNode)
        self.curNode.children.append(newNode)
        self.catalog.append(newNode)
        self.updateTree()

    # 新建文件
    def createFile(self):
        self.item_1 = QListWidgetItem(QIcon("images/file.png"), "新建文件")
        self.listView.addItem(self.item_1)
        self.listView.editLast()
        newNode = CatalogNode(self.item_1.text(),True,self.fat,self.disk,time.localtime(time.time()),self.curNode)
        self.curNode.children.append(newNode)
        self.catalog.append(newNode)
        self.updateTree()

    # 属性视图
    def viewAttribute(self): 
        if len(self.listView.selectedItems()) == 0:
            self.child = attributeForm(self.curNode.name, False,self.curNode.createTime,self.curNode.updateTime,len(self.curNode.children))
            self.child.show()
            return
        else:
            node = self.curNode.children[self.listView.selectedIndexes()[-1].row()]
            if node.isFile:
                self.child = attributeForm(node.name, node.isFile, node.createTime, node.updateTime, 0)
            else:
                self.child = attributeForm(node.name, node.isFile, node.createTime, node.updateTime, len(node.children))
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

            # 只有选中文件时才显示复制选项
            if selectedNode.isFile:
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
            child = QTreeWidgetItem(item)
        elif item.childCount() > len(node.children):
            for i in range(item.childCount()):
                if i == item.childCount()-1:
                    item.removeChild(item.child(i))
                    break
                if item.child(i).text(0) != node.children[i].name:
                    item.removeChild(item.child(i))
                    break

        for i in range(len(node.children)):
            self.updateTreeRecursive(node.children[i], item.child(i))
        self.updateTreeRecursive(node, item)

    def updateTreeRecursive(self, node : CatalogNode, item : QTreeWidgetItem): 
        item.setText(0, node.name)
        if node.isFile:
            item.setIcon(0, QIcon('images/file.png'))
        else:
            if len(node.children) == 0:
                item.setIcon(0, QIcon('images/folder.png'))
            else:
                item.setIcon(0, QIcon('images/folder.png'))
            if item.childCount() < len(node.children):
                child = QTreeWidgetItem(item)
            elif item.childCount() > len(node.children):
                for i in range(item.childCount()):
                    if i == item.childCount()-1:
                        item.removeChild(item.child(i))
                        break
                    if item.child(i).text(0) != node.children[i].name:
                        item.removeChild(item.child(i))
                        break
            for i in range(len(node.children)):
                self.updateTreeRecursive(node.children[i], item.child(i))

    # 建立树
    def buildTree(self): 
        self.tree.clear()
        self.rootItem = self.buildTreeRecursive(self.catalog[0],self.tree)
        self.tree.addTopLevelItem(self.rootItem)
        self.tree.expandAll()

    # 获取数据
    def getData(self, parameter): 
        self.writeFile.data.update(parameter, self.fat, self.disk)
        self.writeFile.updateTime = time.localtime(time.time())

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
        self.listView.clear()

        for i in self.curNode.children:
            if i.isFile:
                self.item_1 = QListWidgetItem(QIcon("images/file.png"), i.name)
                self.listView.addItem(self.item_1)
            else:
                if len(i.children) == 0:
                    self.item_1 = QListWidgetItem(QIcon("images/folder.png"), i.name)
                else:
                    self.item_1 = QListWidgetItem(QIcon("images/folder.png"), i.name)
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

    # 修改复制功能方法，确保只复制文件
    def copyFile(self):
        if len(self.listView.selectedItems()) == 0:
            return
        
        index = self.listView.selectedIndexes()[-1].row()
        node = self.curNode.children[index]
        
        # 确保只复制文件
        if not node.isFile:
            return
        
        self.clipboard = node
        
        # 修改为与其他提示框统一的风格
        reply = QMessageBox()
        reply.setFont(QFont("Times New Roman", 10))
        reply.setWindowTitle('information')
        reply.setWindowIcon(QIcon('images/copy.png'))
        reply.setText(f'File "{self.clipboard.name}" has been copied.')
        reply.setStandardButtons(QMessageBox.Ok)
        buttonOk = reply.button(QMessageBox.Ok)
        buttonOk.setText('ok')
        reply.exec_()

    # 添加粘贴功能
    def pasteFile(self):
        if not self.clipboard:
            return
        
        # 检查目标位置是否已有同名文件/文件夹
        targetName = self.clipboard.name
        for child in self.curNode.children:
            if child.name == targetName:
                targetName += "(副本)"
                break
        
        if self.clipboard.isFile:
            # 复制文件
            data = self.clipboard.data.read(self.fat, self.disk)
            newNode = CatalogNode(targetName, True, self.fat, self.disk, time.localtime(time.time()), self.curNode)
            newNode.data.update(data, self.fat, self.disk)
            self.curNode.children.append(newNode)
            self.catalog.append(newNode)
        else:
            # 复制文件夹
            newNode = CatalogNode(targetName, False, self.fat, self.disk, time.localtime(time.time()), self.curNode)
            self.curNode.children.append(newNode)
            self.catalog.append(newNode)
            self.copyFolderRecursive(self.clipboard, newNode)
        
        # 刷新视图
        self.updateTree()
        self.loadCurFile()

    # 递归复制文件夹
    def copyFolderRecursive(self, sourceNode, targetNode):
        for child in sourceNode.children:
            if child.isFile:
                # 复制文件
                data = child.data.read(self.fat, self.disk)
                newNode = CatalogNode(child.name, True, self.fat, self.disk, time.localtime(time.time()), targetNode)
                newNode.data.update(data, self.fat, self.disk)
                targetNode.children.append(newNode)
                self.catalog.append(newNode)
            else:
                # 复制文件夹
                newNode = CatalogNode(child.name, False, self.fat, self.disk, time.localtime(time.time()), targetNode)
                targetNode.children.append(newNode)
                self.catalog.append(newNode)
                self.copyFolderRecursive(child, newNode)

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

# 主函数
if __name__=='__main__':
    app = QApplication(sys.argv)
    myWindow = myWindow()
    myWindow.show()
    sys.exit(app.exec_())