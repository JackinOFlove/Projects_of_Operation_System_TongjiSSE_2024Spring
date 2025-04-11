'''
------------------------------------------------------
文件名: CatalogModel.py
描述: 目录结构相关的类定义模块
包含: CatalogNode类（目录节点）
------------------------------------------------------
'''

import time
from DiskModel import FCB

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
            