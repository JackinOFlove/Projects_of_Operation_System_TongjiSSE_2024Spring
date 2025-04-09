import sys
import time
from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# 全局变量电梯数量和楼层数量
FLOOR_NUM = 20
ELEVATOR_NUM = 5

# 定义类：电梯界面
class Elevator_UI(QWidget):

    def __init__(self):
        super(Elevator_UI, self).__init__()
        self.initUI()

    def initUI(self):

        # 设置布局
        gridLayout = QGridLayout()

        # 1.设置标签Label
        for i in range(ELEVATOR_NUM):
            elevatorLabel = QLabel('elevator ' + str(i + 1))
            # 设置每个标签的名字
            elevatorLabel.setObjectName('name%d' % i)
            # 设置每个标签的颜色
            elevatorLabel.setStyleSheet("QLabel{background-color:#FFFFFF;\
                                         color:black; height:30;font-size:30px;\
                                         font-family:Times new roman;}")
            elevatorLabel.setAlignment(Qt.AlignCenter)
            gridLayout.addWidget(elevatorLabel, 0, i, 1, 1)

        # 2.设置数码管的LCD
        for elevator in range(ELEVATOR_NUM):
            elevatorLCD = QtWidgets.QLCDNumber(self)  
            elevatorLCD.setGeometry(QtCore.QRect(254 * elevator + 150, 130, 100, 220))  
            # 设置LCD数码管的颜色
            elevatorLCD.setStyleSheet("QLCDNumber{background-color: black; color: #93D5DC;}")  
            # 设置LCD数码管的位数
            elevatorLCD.setDigitCount(2)  
            elevatorLCD.setSegmentStyle(QtWidgets.QLCDNumber.Filled)  
            elevatorLCD.display(1) 
            # 设置每个LCD数码管的名字
            elevatorLCD.setObjectName(f"elevatorLCD{elevator + 1}")  
        
        # 3.设置每个电梯的状态标签
            elevatorState = QtWidgets.QLabel(self)  
            elevatorState.setGeometry(QtCore.QRect(254 * elevator + 30, 130, 120, 220)) 
            # 设置电梯状态标签的颜色和格式 
            elevatorState.setFont(QtGui.QFont("Times new roman", 20, 100))  
            elevatorState.setStyleSheet("QLabel{background-color: black;color: #93D5DC;}")  
            elevatorState.setAlignment(QtCore.Qt.AlignCenter)  
            # 设置每个电梯状态标签的名字
            elevatorState.setObjectName(f"elevatorState{elevator + 1}")  
            # 设置电梯状态的初始标签显示
            elevatorState.setText("Stay")  

        # 4.设置电梯内部按钮
        for j in range(ELEVATOR_NUM):
            for i in range(FLOOR_NUM):
                inner_btn = QPushButton('%d F' % (20 - i))
                # 设置每个电梯内部按钮的名字(第几号电梯的第几层按钮)
                inner_btn.setObjectName(f"Elevator{j + 1}Floor{20 - i}")
                # 设置每个电梯内部按钮的格式
                inner_btn.setStyleSheet('QPushButton{background-color: #5CB3CC; color: black; font: bold 12pt "Times new roman";}'
                                  'QPushButton:hover{background-color: #C3D7DF}'
                                  'QPushButton:pressed{background-color: #C3D7DF}')
                inner_btn.setMinimumSize(30, 20)
                # 设置每个电梯内部按钮的触发点击事件
                inner_btn.clicked.connect(partial(Set_Elevator_Goalfloor, j + 1, 20 - i))
                gridLayout.addWidget(inner_btn, i + 3, j, 1, 1)

        # 5.设置每个电梯的开门键、关门键和报警键
        for k in range(ELEVATOR_NUM):

            open_btn = QPushButton('OPEN')
            close_btn = QPushButton('CLOSE')
            alert_btn = QPushButton('ALERT')

            # 设置每个电梯开门键、关门键和报警键的格式
            open_btn.setStyleSheet('QPushButton{background-color: #EEA5D1;\
                                    color: black; font: bold 12pt "Times new roman";}'
                                   'QPushButton:hover{background-color: #F3D3E7}'
                                   'QPushButton:pressed{background-color: #F3D3E7}')
            close_btn.setStyleSheet('QPushButton{background-color: #EEA5D1;\
                                     color: black; font: bold 12pt "Times new roman";}'
                                    'QPushButton:hover{background-color: #F3D3E7}'
                                    'QPushButton:pressed{background-color: #F3D3E7}')
            alert_btn.setStyleSheet('QPushButton{background-color: #DE2A18;\
                                     color: #FFF143; font: bold 12pt "Times new roman";}'
                                    'QPushButton:hover{background-color: #F0945D}'
                                    'QPushButton:pressed{background-color: #F0945D}')
            
            open_btn.setMinimumSize(10, 10)
            close_btn.setMinimumSize(10, 10)
            alert_btn.setMinimumSize(10, 10)

            # 设置每个电梯开门键的名字和触发事件
            open_btn.setObjectName(f"Elevator_open{k + 1}")
            open_btn.clicked.connect(partial(Elevator_OpenDoor, k + 1))

            # 设置每个电梯关门键的名字和触发事件
            close_btn.setObjectName(f"Elevator_close{k + 1}")
            close_btn.clicked.connect(partial(Elevator_CloseDoor, k + 1))

            # 设置每个电梯报警键的名字和触发事件
            alert_btn.setObjectName(f"Elevator_alert{k + 1}")
            alert_btn.clicked.connect(partial(Set_Elevator_Alert, k + 1))

            gridLayout.addWidget(open_btn, 23, k, 1, 1)
            gridLayout.addWidget(close_btn, 24, k, 1, 1)
            gridLayout.addWidget(alert_btn, 25, k, 1, 1)

        # 6.设置电梯外部上行按钮
        for i in range(20):
            upbtn = QPushButton('▲ %d F' % (20 - i))
            # 设置每个电梯外部上行按钮的名字
            upbtn.setObjectName(f"up_btn{20 - i}")
            # 设置每个电梯外部上行按钮的格式
            upbtn.setStyleSheet('QPushButton{background-color: #CCA4E3;\
                               color: black; font: bold 12pt "Times new roman"}'
                              'QPushButton:hover{background-color: #E9D7DF}'
                              'QPushButton:pressed{background-color: #E9D7DF}')
            upbtn.setMinimumSize(30, 20)
            # 设置电梯外部上行按钮的触发事件
            upbtn.clicked.connect(partial(Set_Outerelevator_Up, 20 - i))
            gridLayout.addWidget(upbtn, i + 6, 6, 1, 1)

        # 6.设置电梯外部下行按钮
        for i in range(1, 21):
            downbtn = QPushButton('▼ %d F' % (21 - i))
            # 设置每个电梯外部下行按钮的名字
            downbtn.setObjectName(f"down_btn{21 - i}")
            # 设置每个电梯外部下行按钮的格式
            downbtn.setStyleSheet('QPushButton{background-color: #CCA4E3;\
                               color: black; font: bold 12pt "Times new roman"}'
                              'QPushButton:hover{background-color: #E9D7DF}'
                              'QPushButton:pressed{background-color: #E9D7DF}')
            downbtn.setMinimumSize(30, 20)
            # 设置电梯外部下行按钮的触发类型
            downbtn.clicked.connect(partial(Set_Outerelevator_Down, 21 - i))
            gridLayout.addWidget(downbtn, i + 5, 7, 1, 1)

        # 7.设置电梯交互信息的文本输出栏
        output = QTextEdit()
        output.setMinimumSize(100, 300)
        # 设置文本输出栏的名字
        output.setObjectName('information')
        # 设置文本输出栏的字体大小
        output.setFontPointSize(10)
        # 设置文本输出栏的格式
        output.setStyleSheet('color:black; border: 1px solid grey;\
                              border-radius:3px; font: 75 10pt "Times new roman";')
        gridLayout.addWidget(output, 2, 6, 4, 2)

        # 8.设置只读状态的介绍说明信息
        note = QTextBrowser()
        text = "2253744林觉凯的电梯调度小程序：\
                \t\t左侧按下电梯内部按键，右侧按下电梯外部按键；\
                同时可以观察电梯运行状态和电梯运行时的交互信息；\
                你可以在需要的时候按下左侧每一台电梯下方的开门键、关门键和报警键。\
                \t\t\t电梯的交互信息如下："
        # 设置介绍说明信息的格式
        note.setStyleSheet('border: 0px solid black; border-radius:3px;\
                            font: 75 10pt "Times new roman";')
        note.setText(text)
        # 设置介绍说明信息的名字
        note.setObjectName('note')
        gridLayout.addWidget(note, 0, 6, 2, 2)

        # 9.设置主窗口的相关信息
        # 设置主窗口的名字
        self.setObjectName("MyWindow")
        self.setLayout(gridLayout)
        # 设置主窗口的标题文字
        self.setWindowTitle('Elevator_dispatching_by_2253744_林觉凯')
        # 设置主窗口的背景颜色
        self.setStyleSheet("background-color: #E3F9FD")
        # 设置主窗口的大小
        self.resize(1800, 1300)
        # 设置主窗口的出现位置
        self.move(200, 15)
        # 主窗口的显示
        self.show()

# 定义类：电梯线程
class Elevator_Thread(QThread):
    # 实例化一个信号对象，传入整型参数
    update_signal = pyqtSignal(int)

    def __init__(self, elevator_num):
        super(Elevator_Thread, self).__init__()
        self.elevator_num = elevator_num
        # 将信号与槽函数Elevator_Update连接
        self.update_signal.connect(Elevator_Update)

    def run(self):
        # 电梯线程处在永真循环中
        while True:
            # 如果该电梯没有报警而且应该开门：电梯停下并且开门
            if not Elevator_Alert[self.elevator_num - 1] and Elevator_Should_open[self.elevator_num - 1]:

                # 用findChild函数找到主界面上的外部电梯上行按钮、外部电梯下行按钮、该电梯楼层的内部按钮和该电梯的编号
                Up_button = MyWindow.findChild(QPushButton, f"up_btn{Elevator_Floor[self.elevator_num - 1]}")
                Down_button = MyWindow.findChild(QPushButton, f"down_btn{Elevator_Floor[self.elevator_num - 1]}")
                Num_button = MyWindow.findChild(QPushButton, f"Elevator{self.elevator_num}Floor{Elevator_Floor[self.elevator_num - 1]}")
                Label = MyWindow.findChild(QLabel, f"elevatorState{self.elevator_num}")

                # 输出的交互信息更新
                updateInfo = MyWindow.findChild(QTextEdit, 'information')
                # 代码的健壮性
                if updateInfo is not None:
                    updateInfo.append(f"第{self.elevator_num}号电梯到达第{Elevator_Floor[self.elevator_num - 1]}层")
                print(f"第{self.elevator_num}号电梯到达第{Elevator_Floor[self.elevator_num - 1]}层")

                # 恢复外部电梯上行键的格式
                if Up_button:
                    Up_button.setStyleSheet('QPushButton{background-color: #CCA4E3;\
                                             color: black; font: bold 12pt "Times new roman";}'
                                            'QPushButton:hover{background-color: #E9D7DF}'
                                            'QPushButton:pressed{background-color: #E9D7DF}')

                # 恢复外部电梯下行键的格式
                if Down_button:
                    Down_button.setStyleSheet('QPushButton{background-color: #CCA4E3;\
                                               color: black; font: bold 12pt "Times new roman";}'
                                              'QPushButton:hover{background-color: #E9D7DF}'
                                              'QPushButton:pressed{background-color: #E9D7DF}')

                # 恢复该楼层电梯内部按钮的格式
                if Num_button:
                    Num_button.setStyleSheet('QPushButton{background-color: #5CB3CC;\
                                              color: black; font: bold 12pt "Times new roman";}'
                                             'QPushButton:hover{background-color: #C3D7DF}'
                                             'QPushButton:pressed{background-color: #C3D7DF}')

                # 该楼层电梯开门效果的设计
                if Label:
                    # 动画效果：先变色，再显示文字
                    Label.setStyleSheet("QLabel{background-color: white; color: white;}")
                    QApplication.processEvents()  # 立即更新UI
                    time.sleep(0.2)
                    
                    Label.setFont(QtGui.QFont("Times new roman", 20, 100))  
                    Label.setText("Open")  
                    Label.setStyleSheet("QLabel{background-color: white; color: #5CB3CC;}")
                    
                # 开门事件延迟设置
                time.sleep(1)

                # 开门后关门的效果设计
                if Label:
                    # 动画效果：先变色，再显示文字
                    Label.setStyleSheet("QLabel{background-color: black; color: black;}")
                    QApplication.processEvents()  # 立即更新UI
                    time.sleep(0.2)
                    
                    Label.setStyleSheet("QLabel{background-color: black; color: #93D5DC;}")  
                    Label.setText("Stay") 
                
                Elevator_Should_open[self.elevator_num - 1] = False  

            # 发送信号给槽函数进行全局页面、后端电梯信息的更新
            self.update_signal.emit(self.elevator_num)  
            # 延迟效果的设计
            time.sleep(1)

# 电梯状态更新函数
def Elevator_Update(elevator_num):
    # 当电梯没有报警时对电梯进行更新
    if not Elevator_Alert[elevator_num - 1]:

        # 如果电梯处于停留状态0(没有上下行任务)
        if Elevator_State[elevator_num - 1] == 0:
            pass
        # 如果电梯处于下行状态-1
        elif Elevator_State[elevator_num - 1] == -1:
            # 如果这时已经到达最低层一层
            if Elevator_Floor[elevator_num - 1] == 1:
                # 设置当前电梯楼层为1
                Elevator_Floor[elevator_num - 1] = 1
            # 电梯下行一层
            else:
                Elevator_Floor[elevator_num - 1] -= 1
        # 如果电梯处于上行状态1
        else:
            # 如果这时已经到达最高层20层
            if Elevator_Floor[elevator_num - 1] == 20:
                # 设置当前电梯楼层为20
                Elevator_Floor[elevator_num - 1] = 20
            # 电梯上行一层
            else:
                Elevator_Floor[elevator_num - 1] += 1

        # 更新电梯的LCD电子显示管
        UpdateLCDnumber = MyWindow.findChild(QLCDNumber, f"elevatorLCD{elevator_num}")
        if UpdateLCDnumber:
            # 添加数字变化动画
            current_value = UpdateLCDnumber.intValue()
            target_value = Elevator_Floor[elevator_num - 1]
            
            if current_value != target_value:
                # 平滑过渡到新数字
                UpdateLCDnumber.display(target_value)
                
        # 更新电梯的标签信息
        Set_Elevatorlabel(elevator_num)

        # 如果当前电梯楼层对于该电梯的目标楼层或是电梯外部按钮的目标楼层
        if (Elevator_Floor[elevator_num - 1] in Elevator_Target[elevator_num - 1] or 
            (Elevator_Floor[elevator_num - 1] in Elevator_Outer)):
            # 这时电梯应该开门
            Elevator_Should_open[elevator_num - 1] = True
            # 电梯外部楼层的楼层请求集中删去该层请求
            Elevator_Outer.discard(Elevator_Floor[elevator_num - 1])
        # 该电梯的请求楼层中删去该楼层请求
        Elevator_Target[elevator_num - 1].discard(Elevator_Floor[elevator_num - 1])

        # 计算该电梯剩余楼层任务
        LeftFloors_to_go = len(Elevator_Target[elevator_num - 1])
        HighestFloor_to_go = -9 if LeftFloors_to_go == 0 else max(Elevator_Target[elevator_num - 1])
        LowestFloor_to_go = 999 if LeftFloors_to_go == 0 else min(Elevator_Target[elevator_num - 1])

        # 如果电梯正处于下行状态
        if Elevator_State[elevator_num - 1] == -1:
            # 此时没有其他任务了
            if LeftFloors_to_go == 0:
                # 将电梯状态设为停留状态
                Elevator_State[elevator_num - 1] = 0
            # 如果剩余任务的楼层高于当前所在楼层
            elif LowestFloor_to_go > Elevator_Floor[elevator_num - 1]:
                # 电梯状态设为上行状态
                Elevator_State[elevator_num - 1] = 1

        # 如果电梯正处于停留状态而且有目标任务
        if Elevator_State[elevator_num - 1] == 0 and LeftFloors_to_go != 0:
            # 比较当前所在楼层和目标任务楼层大小决定上行还是下行
            if HighestFloor_to_go > Elevator_Floor[elevator_num - 1]:
                Elevator_State[elevator_num - 1] = 1
            elif LowestFloor_to_go < Elevator_Floor[elevator_num - 1]:
                Elevator_State[elevator_num - 1] = -1

        # 如果电梯正处于上行状态
        if Elevator_State[elevator_num - 1] == 1:
            # 此时没有其他任务了
            if LeftFloors_to_go == 0:
                # 将电梯状态设为停留状态
                Elevator_State[elevator_num - 1] = 0
            # 如果剩余任务的楼层低于当前所在楼层
            elif HighestFloor_to_go < Elevator_Floor[elevator_num - 1]:
                # 电梯状态设为下行状态
                Elevator_State[elevator_num - 1] = -1

# 电梯状态标签更新函数
def Set_Elevatorlabel(elevator_num):
    # 找到该电梯的状态标签控件
    label = MyWindow.findChild(QLabel, f"elevatorState{elevator_num}")  
    if not label:
        return

    # 如果电梯处于停留状态，可能是Stay或者Stall
    if Elevator_State[elevator_num - 1] == 0:
        label.setFont(QtGui.QFont("Times new roman", 20, 100))  
        label.setText(f"{'Stall' if Elevator_Alert[elevator_num - 1] else 'Stay'}")  
    # 电梯上行状态和下行状态的箭头标签
    else:
        # 添加动画效果
        current_text = label.text()
        new_text = '↑' if Elevator_State[elevator_num - 1] == 1 else '↓'
        
        if current_text != new_text:
            # 过渡动画
            label.setStyleSheet("QLabel{background-color: black; color: transparent;}")
            QApplication.processEvents()  # 立即更新UI
            time.sleep(0.1)
            
            label.setFont(QtGui.QFont("Times new roman", 40, 100))
            label.setText(new_text)
            label.setStyleSheet("QLabel{background-color: black; color: #93D5DC;}")

# 电梯开门按钮设置
def Elevator_OpenDoor(elevator_num):
    # 找到该电梯的开门按钮控件
    updateInfo = MyWindow.findChild(QTextEdit, 'information')

    # 如果电梯处于停留状态而且没有报警：可以开门
    if Elevator_State[elevator_num - 1] == 0 and not Elevator_Alert[elevator_num - 1]:
        Elevator_Should_open[elevator_num - 1] = True
        # 代码的健壮性，并且文本输出电梯信息
        if updateInfo is not None:
            updateInfo.append(f"第{elevator_num}号电梯门开")
        print(f"第{elevator_num}号电梯门开")
    # 如果电梯不处于停留状态有两种情况
    else:
        # 如果此时电梯报警：不开门
        if Elevator_Alert[elevator_num - 1]:
            # 代码的健壮性，并且文本输出电梯信息
            if updateInfo is not None:
                updateInfo.append(f"第{elevator_num}号电梯报警中，不开门")
            print(f"第{elevator_num}号电梯报警中，不开门")
        # 如果此时电梯在运行中：也不开门
        else:
            # 代码的健壮性，并且文本输出电梯信息
            if updateInfo is not None:
                updateInfo.append(f"第{elevator_num}号电梯正在运行中，不开门")
            print(f"第{elevator_num}号电梯正在运行中，不开门")

# 电梯关门按钮设置
def Elevator_CloseDoor(elevator_num):
    # 找到该电梯的开门按钮控件
    updateInfo = MyWindow.findChild(QTextEdit, 'information')

    # 如果电梯处于停留状态而且没有报警：可以关门
    if Elevator_State[elevator_num - 1] == 0 and not Elevator_Alert[elevator_num - 1]:
        Elevator_Should_open[elevator_num - 1] = False
        # 代码的健壮性，并且文本输出电梯信息
        if updateInfo is not None:
            updateInfo.append(f"第{elevator_num}号电梯门关")
        print(f"第{elevator_num}号电梯门关")
    # 如果电梯不处于停留状态有两种情况
    else:
        # 如果此时电梯报警：不关门
        if Elevator_Alert[elevator_num - 1]:
            # 代码的健壮性，并且文本输出电梯信息
            if updateInfo is not None:
                updateInfo.append(f"第{elevator_num}号电梯报警中，不关门")
            print(f"第{elevator_num}号电梯报警中，不关门")
        # 如果此时电梯在运行中：告知电梯已经关门
        else:
            # 代码的健壮性，并且文本输出电梯信息
            if updateInfo is not None:
                updateInfo.append(f"第{elevator_num}号电梯正在运行中，已关门")
            print(f"第{elevator_num}号电梯正在运行中，已关门")

# 电梯报警按钮的设置
def Set_Elevator_Alert(elevator_num):
    # 找到该电梯的报警按钮和状态标签
    AlertButton = MyWindow.findChild(QPushButton, f"Elevator_alert{elevator_num}")
    StallLabel = MyWindow.findChild(QLabel, f"elevatorState{elevator_num}")
    
    if not AlertButton or not StallLabel:
        return

    # 先前没报警的电梯按下报警键：报警
    if not Elevator_Alert[elevator_num - 1]:
        Elevator_Alert[elevator_num - 1] = True

        # 设置报警后的报警按钮格式
        AlertButton.setStyleSheet('QPushButton{background-color: #F0945D;\
                                   color: #FFF143; font: bold 12pt "Times new roman";}'
                                  'QPushButton:hover{background-color: #DE2A18}'
                                  'QPushButton:pressed{background-color: #DE2A18}')
        
        # 设置报警后的电梯状态标签 - 添加动画效果
        StallLabel.setStyleSheet("QLabel{background-color: black; color: transparent;}")
        QApplication.processEvents()  # 立即更新UI
        time.sleep(0.2)
        
        StallLabel.setFont(QtGui.QFont("Times new roman", 20, 100))
        StallLabel.setStyleSheet("QLabel{background-color: red; color: yellow;}")
        StallLabel.setText("Stall")

        # 代码的健壮性，并且输出电梯信息文本
        updateInfo = MyWindow.findChild(QTextEdit, 'information')
        if updateInfo is not None:
            updateInfo.append(f"第{elevator_num}号电梯报警!该电梯暂停使用！")
        print(f"第{elevator_num}号电梯报警!该电梯暂停使用！")

        # 该电梯剩余外部楼层任务(可以认为是外部任务)分配给别的电梯,当前楼层内的内部任务根据常识无法分配
        Leftneeded_Floor = set()
        for floor in Elevator_Target[elevator_num - 1]:
            if floor in Elevator_Outer:
                # 该数组存储剩余外部楼层任务和当前哪个电梯距离相近
                Elevator_Floor_gap = []
                for elev in range(ELEVATOR_NUM):
                    Elevator_Floor_gap.append(10000 if Elevator_Alert[elev] else abs(Elevator_Floor[elev] - floor))
                
                # 找到最近的电梯转移任务
                NewElevator = Elevator_Floor_gap.index(min(Elevator_Floor_gap))
                Leftneeded_Floor.add(floor)
                Elevator_Target[NewElevator].add(floor)

                # 代码的健壮性，并且输出电梯信息文本
                # 更新信息显示区域
                updateInfo = MyWindow.findChild(QTextEdit, 'information')
                if updateInfo is not None:
                    updateInfo.append(f"第{elevator_num}号电梯要去{floor}楼的任务因报警而分配给了第{NewElevator + 1}号电梯")
                print(f"第{elevator_num}号电梯要去{floor}楼的任务因报警而分配给了第{NewElevator + 1}号电梯")

        # 将该报警电梯的外部楼层任务从该电梯任务中删去
        for LeftFloor in Leftneeded_Floor:  
            Elevator_Target[elevator_num - 1].discard(LeftFloor)
        if len(Elevator_Target[elevator_num - 1]) == 0: 
            Elevator_State[elevator_num - 1] = 0

    # 先前报警的电梯按下报警键：解除报警
    else:
        Elevator_Alert[elevator_num - 1] = False

        # 设置解除报警按钮格式
        AlertButton.setStyleSheet('QPushButton{background-color: #DE2A18;\
                                   color: #FFF143; font: bold 12pt "Times new roman";}'
                                  'QPushButton:hover{background-color: #F0945D}'
                                  'QPushButton:pressed{background-color: #F0945D}')
        
        # 设置解除报警电梯标签
        StallLabel.setFont(QtGui.QFont("Times new roman", 20, 100))
        StallLabel.setStyleSheet("QLabel{background-color: black; color: #93D5DC;}")
        StallLabel.setText("Stay")
        
        # 更新电梯标签
        Set_Elevatorlabel(elevator_num)  
        
        # 代码的健壮性，并且输出电梯信息文本
        updateInfo = MyWindow.findChild(QTextEdit, 'information')
        if updateInfo is not None:
            updateInfo.append(f"第{elevator_num}号电梯已解除报警状态！")
        print(f"第{elevator_num}号电梯已解除报警状态！")

# 电梯内部楼层任务目标
def Set_Elevator_Goalfloor(elevator_num, goal_floor):
    # 如果当前电梯楼层等于电梯内部任务楼层
    if Elevator_Floor[elevator_num - 1] == goal_floor:
        # 代码的健壮性，并且输出电梯信息文本
        updateInfo = MyWindow.findChild(QTextEdit, 'information')
        if updateInfo is not None:
            updateInfo.append(f"第{elevator_num}号电梯就在第{goal_floor}层")
        print(f"第{elevator_num}号电梯就在第{goal_floor}层")
        return

    # 相应按下内部楼层按钮的格式
    ClickButton = MyWindow.findChild(QPushButton, f"Elevator{elevator_num}Floor{goal_floor}")
    ClickButton.setStyleSheet('QPushButton{background-color: #C3D7DF;\
                               color:black; font: bold 12pt "Times new roman";}')

    # 更新电梯状态标签
    Set_Elevatorlabel(elevator_num)

    # 将该内部电梯请求楼层加入该电梯的任务数组中
    Elevator_Target[elevator_num - 1].add(goal_floor)
    # 代码的健壮性，并且输出电梯信息文本
    updateInfo = MyWindow.findChild(QTextEdit, 'information')
    if updateInfo is not None:
        updateInfo.append(f"第{elevator_num}号电梯要去第{goal_floor}层")
    print(f"第{elevator_num}号电梯要去第{goal_floor}层")

# 电梯外部上行按钮任务
def Set_Outerelevator_Up(goal_floor):
    # 如果有楼层处于请求楼层，开门
    for elevator in range(ELEVATOR_NUM):
        if Elevator_Floor[elevator] == goal_floor and Elevator_State[elevator] == 0:
            # 代码的健壮性，并且输出电梯信息文本
            updateInfo = MyWindow.findChild(QTextEdit, 'information')
            if updateInfo is not None:
                updateInfo.append(f"电梯{elevator + 1}已在{goal_floor}层")
            print(f"电梯{elevator + 1}已在{goal_floor}层")
            Elevator_Should_open[elevator] = True
            return

    # 电梯外部上行按钮按下的格式设计
    ClickButton = MyWindow.findChild(QPushButton, f"up_btn{goal_floor}")
    ClickButton.setStyleSheet('QPushButton{background-color: #E9D7DF;\
                               color:black; font: bold 12pt "Times new roman";}')

    # 计算每部电梯楼层与当前外部请求楼层的差值
    Floor_Elevator_gap = []
    for elevator in range(ELEVATOR_NUM):
        Floor_Elevator_gap.append(10000 if Elevator_Alert[elevator] else abs(Elevator_Floor[elevator] - goal_floor))

    # 选择最近的楼层并且加入该电梯的目标数组中
    ChooseElevator = Floor_Elevator_gap.index(min(Floor_Elevator_gap))
    Elevator_Target[ChooseElevator].add(goal_floor)
    Elevator_Outer.add(goal_floor)

    # 代码的健壮性，并且输出电梯信息文本
    updateInfo = MyWindow.findChild(QTextEdit, 'information')
    if updateInfo is not None:
        updateInfo.append(f"第{ChooseElevator + 1}号电梯被分配到{goal_floor}层的任务")
    print(f"第{ChooseElevator + 1}号电梯被分配到{goal_floor}层的任务")

# 电梯外部下行按钮任务
def Set_Outerelevator_Down(goal_floor):
    # 如果有楼层处于请求楼层，开门
    for elevator in range(ELEVATOR_NUM):
        if Elevator_Floor[elevator] == goal_floor and Elevator_State[elevator] == 0:
            # 代码的健壮性，并且输出电梯信息文本
            updateInfo = MyWindow.findChild(QTextEdit, 'information')
            if updateInfo is not None:
                updateInfo.append(f"电梯{elevator + 1}已在{goal_floor}层")
            print(f"电梯{elevator + 1}已在{goal_floor}层")
            Elevator_Should_open[elevator] = True
            return

    # 电梯外部下行按钮按下的格式设计
    ClickButton = MyWindow.findChild(QPushButton, f"down_btn{goal_floor}")
    ClickButton.setStyleSheet('QPushButton{background-color: #E9D7DF;\
                               color:black; font: bold 12pt "Times new roman";}')

    # 计算每部电梯楼层与当前外部请求楼层的差值
    Floor_Elevator_gap = []
    for elevator in range(ELEVATOR_NUM):
        Floor_Elevator_gap.append(10000 if Elevator_Alert[elevator] else abs(Elevator_Floor[elevator] - goal_floor))

    # 选择最近的楼层并且加入该电梯的目标数组中
    ChooseElevator = Floor_Elevator_gap.index(min(Floor_Elevator_gap))
    Elevator_Target[ChooseElevator].add(goal_floor)
    Elevator_Outer.add(goal_floor)

    # 代码的健壮性，并且输出电梯信息文本
    updateInfo = MyWindow.findChild(QTextEdit, 'information')
    if updateInfo is not None:
        updateInfo.append(f"第{ChooseElevator + 1}号电梯被分配到{goal_floor}层的任务")
    print(f"第{ChooseElevator + 1}号电梯被分配到{goal_floor}层的任务")

# main函数
if __name__ == '__main__':

    app = QApplication(sys.argv)
    # 实例化Elevator_UI：MyWindow
    MyWindow = Elevator_UI()

    # 每部电梯是否报警
    Elevator_Alert = []
    # 每部电梯当前所在楼层
    Elevator_Floor = []
    # 每部电梯门是否该开
    Elevator_Should_open = []
    # 每部电梯的目标楼层
    Elevator_Target = []
    # 每部电梯的当前状态：-1下行，0停留，1上行
    Elevator_State = []
    # 电梯外部任务请求
    Elevator_Outer = set([])

    for i in range(ELEVATOR_NUM):
        # 每部电梯初始不报警
        Elevator_Alert.append(False)
        # 每部电梯初始楼层设为1
        Elevator_Floor.append(1)
        # 每部电梯初始状态关门
        Elevator_Should_open.append(False)
        # 每部电梯初始无目标任务楼层
        Elevator_Target.append(set([]))
        # 每部电梯初始处在停留状态
        Elevator_State.append(0)

    # 创建五个电梯线程
    Elevators = []
    for i in range(ELEVATOR_NUM):
        Elevators.append(Elevator_Thread(i + 1))

    # 电梯线程开始
    for i in range(ELEVATOR_NUM):
        Elevators[i].start()

    # 进入程序的主循环
    sys.exit(app.exec_())