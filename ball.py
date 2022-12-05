from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(50, 40)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.toolButton = QToolButton(Form)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setGeometry(QRect(10, 10, 31, 31))
        icon = QIcon()
        icon.addFile(u"./icons/run.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton.setIcon(icon)
        QMetaObject.connectSlotsByName(Form)
    # setupUi

    # retranslateUi
from PySide2.QtWidgets import QApplication,QMainWindow
from PySide2.QtCore import Qt
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 使用ui文件导入定义界面类
        self.ui = Ui_Form()
        # 初始化界面
        self.ui.setupUi(self)
        # 设置窗口无边框； 设置窗口置顶；
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 设置窗口背景透明
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置透明度(0~1)   
        self.setWindowOpacity(0.9)
        # 设置鼠标为手状
        self.setCursor(Qt.PointingHandCursor)
        self.ui.toolButton.clicked.connect(print)
    #鼠标按下时，记录鼠标相对窗口的位置
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # event.pos() 鼠标相对窗口的位置
            # event.globalPos() 鼠标在屏幕的绝对位置
            self._startPos = event.pos()
    # 鼠标移动时，移动窗口跟上鼠标；同时限制窗口位置，不能移除主屏幕
    def mouseMoveEvent(self, event: QMouseEvent):
        # event.pos()减去最初相对窗口位置，获得移动距离(x,y)
        self._wmGap = event.pos() - self._startPos
        # 移动窗口，保持鼠标与窗口的相对位置不变
        # 检查是否移除了当前主屏幕
        # 左方界限
        final_pos = self.pos() + self._wmGap
        if self.frameGeometry().topLeft().x() + self._wmGap.x() <= 0:
            final_pos.setX(0)
        # 上方界限
        if self.frameGeometry().topLeft().y() + self._wmGap.y() <= 0:
            final_pos.setY(0)
        # 右方界限

        self.move(final_pos)

if __name__ == '__main__':
    ball =MainWindow()
    ball.show()
    app.exec_()