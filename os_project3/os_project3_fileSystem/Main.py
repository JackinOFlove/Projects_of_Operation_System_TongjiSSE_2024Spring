'''
------------------------------------------------------
文件名: Main.py
描述: 文件系统程序入口
功能: 初始化应用程序并解决pickle序列化兼容性问题
------------------------------------------------------
'''

import sys
from PyQt5.QtWidgets import QApplication
from FileSystemApp import myWindow
from DiskModel import FAT, Block, FCB
from CatalogModel import CatalogNode

# 创建类别别名，让pickle能找到原来的类路径
sys.modules['__main__'].FAT = FAT
sys.modules['__main__'].Block = Block
sys.modules['__main__'].FCB = FCB
sys.modules['__main__'].CatalogNode = CatalogNode

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fileSystem = myWindow()
    fileSystem.show()
    sys.exit(app.exec_())
    