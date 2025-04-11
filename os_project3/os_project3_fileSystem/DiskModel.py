'''
------------------------------------------------------
文件名: DiskModel.py
描述: 磁盘存储结构相关的类定义模块
包含: Block类（物理块）、FAT类（文件分配表）、FCB类（文件控制块）
功能: 磁盘空间分配、文件物理存储读写等底层操作
------------------------------------------------------
'''

import pickle
import time

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
