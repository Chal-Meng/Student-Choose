from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMessageBox, QApplication, QInputDialog, QFileDialog, QCheckBox, QAbstractItemView, QApplication
from PySide2.QtCore import QStringListModel, Qt, QCoreApplication, QTimer, Signal, Slot
from random import choice, randint
from loguru import logger
from json import load, dump, JSONDecodeError
from typing import List
from functools import partial
from sys import exit
from ball import MainWindow


def changeDir():
    """切换工作目录"""
    from os import sep, chdir
    from sys import argv
    chdir(sep.join(argv[0].split(sep)[:-1]))


changeDir()
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication([])
names = []
ball = MainWindow()  # 小窗
isLog: bool = True


def handle_JSON_Error(filename: str):
    '''文件格式错误就删除重来'''
    from os import remove
    remove(filename)
    QMessageBox.critical(main.ui, '错误', f'{filename}文件似乎被人损坏了。请重新启动我这个程序')


def getNames(outError: bool = True):
    '''从文件中获取当前等待点名的列表
    outError:输出不输出提示'''
    global classNames, names
    # 获取现在的名单
    try:
        with open('./settings/waiting.json', encoding='utf-8') as f:
            names = load(f)['waiting']
    except FileNotFoundError:
        names = []
        rebuild_names()


def rebuild_names(*args, **kwargs):
    """重建等待点名列表"""
    global classNames, names
    try:
        with open('./settings/name_sheet.json', encoding='utf-8') as f:
            names_all = load(f)  # 获取总的名字
    except FileNotFoundError:
        with open('./settings/name_sheet.json', encoding='utf-8', mode='w') as f:
            dump(dict(), f, ensure_ascii=False)
    except JSONDecodeError:
        handle_JSON_Error('./settings/name_sheet.json')
    # 选择哪个班
    try:
        with open('./settings/settings.json', encoding='utf-8') as f:
            choose: List[str] = load(f)['choose']
            if len(choose) == 0:  # 没指定
                QMessageBox.critical(
                    main.ui, '警告', '没有设置点名的班级和范围。请点确定后从设置里面调一下。')
                classNames = []
                names = []
    except JSONDecodeError:
        handle_JSON_Error('./settings/settings.json')
    else:
        names = []
        for className, Name in names_all.items():
            if className in choose:
                names.extend(Name)
        classNames = choose
        logger.debug('rebuild')
        with open("./settings/waiting.json", encoding='utf-8', mode='w') as f:
            dump({"waiting": names}, f, ensure_ascii=False, indent=4)


def update_names(removing_name: str):
    """更新姓名列表并且写入文件"""
    names.remove(removing_name)
    with open("./settings/waiting.json", encoding='utf-8', mode='w') as f:
        dump({"waiting": names}, f, ensure_ascii=False, indent=4)


def getIsLog() -> bool:
    """配置是否记录日志"""
    global isLog
    try:
        with open('./settings/settings.json', encoding='utf-8') as f:
            isLog = load(f)['log']
            if isLog:
                logger.add('.\log\点名记录_{time:MM-DD HH-mm}.log',
                           format='<green>{time:MM-DD HH:mm:ss}</green>--<level>{message}</level>', rotation='1 day', retention='1 month')
            return isLog
    except (KeyError, FileNotFoundError):  # 未指定
        main.ui.statusbar.showMessage('已默认开启点名记录功能，点下的名会存下来。可以自己关闭。')
        with open('./settings/settings.json', encoding='utf-8', mode='w') as f:
            dump({'log': True}, f, ensure_ascii=False)
    except JSONDecodeError:  # 编码错误
        handle_JSON_Error('./settings/settings.json')


def randomColor() -> str:
    """返回以“#”开头的随机颜色字符串"""
    def randomHex(min: int, max: int) -> str:
        """返回不包含“0x”的十六进制随机字符串"""
        return hex(randint(min, max))[2:]
    return '#'+''.join((randomHex(100, 255), randomHex(100, 255), randomHex(100, 255)))


def openLogPath():
    """打开日志的文件夹"""
    from os.path import realpath
    from webbrowser import open
    open(realpath('./log'))


class MainWindow:
    """主窗口
    self.ui是窗口定义
    """

    def __init__(self) -> None:
        """窗口初始化"""
        self.ui = QUiLoader().load('UI/main.ui')  # 主窗口
        # 点名事件
        self.ui.NameButton.clicked.connect(partial(self.next, showResult=True))
        # 连点事件
        self.ui.seq2.triggered.connect(partial(self.many, n=2))
        self.ui.seq5.triggered.connect(partial(self.many, n=5))
        self.ui.seq10.triggered.connect(partial(self.many, n=10))
        self.ui.seq_custom.triggered.connect(partial(self.many, n=0))
        # 查看日志
        self.ui.WatchLog.triggered.connect(self.openLogPath)
        self.ui.Changelog.triggered.connect(self.changeLog)
        # 切换/添加班级
        self.ui.changeClass.triggered.connect(self.changeClass)
        self.ui.EditClass.triggered.connect(self.editClass)
        # 切换小窗
        self.ui.changeBall.clicked.connect(self.changeBall)
        # 重置
        self.ui.reset.clicked.connect(rebuild_names)
        self.ui.reset.clicked.connect(self.update_length)
        # 计时器
        self.timer = QTimer(self.ui)
        self.timer.timeout.connect(self.flash)

        self.update_length()

    def flash(self):
        """闪光"""
        name = choice(names)
        self.ui.NameButton.setStyleSheet(
            f"background-color:{randomColor()}")
        self.ui.NameButton.setText(name)

    def next(self, showResult: bool = True) -> str:
        """点名并记录日志"""
        if len(names) == 0:  # 用光了
            rebuild_names()

        if self.ui.NameButton.property('flashing'):  # 正在闪，应该停下来
            self.ui.NameButton.setProperty('flashing', False)
            self.timer.stop()
            name = choice(names)
            if isLog:
                logger.info(name)
            if showResult:
                self.ui.NameButton.setStyleSheet(
                    f"background-color:{randomColor()}")
                self.ui.NameButton.setText(name)
            # 从名单中移除
            update_names(name)
            self.update_length()
            return name
        else:
            self.ui.NameButton.setProperty('flashing', True)
            self.timer.start(50)

    def many(self, n: int) -> None:
        """连点，多次调用next()实现"""
        if n == 0:
            n, ok = QInputDialog.getInt(
                self.ui, '输入', '请输入连点个数', value=5, minValue=1, maxValue=100)
            if not ok:
                return
        name = []
        logger.success('开始连续点{}个名字！', n)
        for i in range(n):
            if len(names) == 0:
                rebuild_names()
            chosen_name = choice(names)
            update_names(chosen_name)
            name.append(chosen_name)
        logger.success('连续点{}个名字完毕！', n)
        self.update_length()
        result = QMessageBox.question(
            self.ui, '连点结果,保存吗？', '\n'.join(name))  # 保存
        if result == QMessageBox.StandardButton.Yes:
            filename, ok = QFileDialog.getSaveFileName(
                self.ui, '保存点名结果', filter='文本文件 (*.txt)')
            if filename == '':
                return  # 中途取消
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(name))

    def changeClass(self) -> None:
        w = ChangeWindow()

    def editClass(self) -> None:
        w = EditWindow()
        w.ui.show()
        w.ui.exec()

    def update_length(self) -> None:
        self.ui.statusbar.showMessage(f'当前名单长度：{len(names)}')

    def changeLog(self) -> None:
        """切换是否显示"""
        with open('./settings/settings.json', encoding='utf-8') as f:
            old_set = load(f)
        old = old_set["log"]
        global isLog
        isLog = False if old else True  # 反过来
        old_set["log"] = isLog
        with open('./settings/settings.json', encoding='utf-8', mode='w') as f:
            dump(old_set, f, ensure_ascii=False)
        QMessageBox.about(self.ui, '成功', f"已切换为{''if isLog else '不'}显示日志")
        return isLog

    def openLogPath(self):
        """打开日志的文件夹"""
        from os.path import realpath
        from webbrowser import open
        open(realpath('./log'))

    def changeThis(self):
        """隐藏悬浮窗，打开主窗口"""
        self.ui.show()
        ball.hide()

    def changeBall(self):
        """隐藏主窗口，打开悬浮窗"""
        self.ui.hide()
        ball.show()


class ChangeWindow:
    """控制选择哪个班的窗口"""

    def __init__(self) -> None:
        self.ui = QUiLoader().load('UI/changeRange.ui')
        rebuild_names()
        # self.ui.setParent(main.ui)
        with open('./settings/name_sheet.json', encoding='utf-8') as f:
            all_name: dict = load(f)
        self.boxes = {}
        if not all_name:  # 还没设置班级
            QMessageBox.critical(main.ui, '错误', '还没有名单！请在主界面的“设置”中新建班级、导入名单。')
            return
        for class_name in all_name.keys():
            self.boxes[class_name] = QCheckBox(class_name, parent=self.ui)
            self.ui.ChecksLayout.addWidget(self.boxes[class_name])
            if class_name in classNames:
                self.boxes[class_name].setChecked(True)  # 提前设好
        self.ui.buttonBox.accepted.connect(self.submit)
        self.ui.show()
        self.ui.exec()

    def submit(self) -> None:
        """提交的函数"""
        global classNames, names
        classNames.clear()
        for class_name, Check in self.boxes.items():
            if Check.checkState():
                classNames.append(class_name)
        names.clear()
        with open('./settings/name_sheet.json', encoding='utf-8') as f:
            names_all = load(f)  # 获取总的名字
        for className in classNames:
            names.extend(names_all[className])
        if self.ui.IsRemember.checkState():  # 保存设置
            with open('./settings/settings.json', encoding='utf-8') as f:
                old_set = load(f)
            old_set['choose'] = classNames
            with open('./settings/settings.json', encoding='utf-8', mode='w') as f:
                dump(old_set, f, ensure_ascii=False,)


class EditWindow:
    """编辑班级的窗口"""
    edit_class_name = ''

    def __init__(self) -> None:
        self.ui = QUiLoader().load("./UI/EditClass.ui")
        # 配置左侧的
        self.slm = QStringListModel()  # 保存班级名的东西
        with open('./settings/name_sheet.json', encoding='utf-8') as f:
            self.all_name: dict = load(f)
        self.all_ClassNames = list(self.all_name.keys())  # 把班级名提前保存下来
        self.slm.setStringList(self.all_ClassNames)
        self.ui.listView.setModel(self.slm)
        self.ui.listView.clicked.connect(self.clickName)
        self.ui.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置右侧
        self.ui.NamesText.textChanged.connect(self.textChanged)
        # 设置增加减少班级
        self.ui.addButton.clicked.connect(self.addClass)
        self.ui.delButton.clicked.connect(self.delClass)
        # 右边不准编辑
        self.ui.NamesText.setEnabled(False)
        self.ui.pushButton.clicked.connect(self.saveResult)

    def addClass(self) -> None:
        """添加新的班级"""
        newClassName, okPressed = QInputDialog.getText(
            self.ui, '新建班级', '输入新的班级的名字：')
        if not okPressed:
            return  # 没给名字
        self.all_ClassNames.append(newClassName)
        self.slm.setStringList(self.all_ClassNames)  # 给slm加一项
        self.all_name[newClassName] = []
        self.ui.listView.setCurrentIndex(
            self.slm.index(len(self.all_ClassNames), 0))
        self.ui.PromptLabel.setText('请输入或粘贴名单。')

    def delClass(self) -> None:
        """删除当前班级"""
        be_deleted = self.ui.listView.selectionModel().selectedIndexes()[
            0].data()  # 获取当前选择的班级名字
        if QMessageBox.question(self.ui, '确定吗', f'确定删除“{be_deleted}”吗？此操作不可逆！') == QMessageBox.StandardButton.Yes:
            be_deleted_index = self.all_ClassNames.index(be_deleted)
            self.all_ClassNames.pop(be_deleted_index)  # 从左侧删掉
            self.slm.removeRow(be_deleted_index)
            # 从储存的选项列表去掉
            with open('./settings/settings.json', encoding='utf-8') as f:
                old_set = load(f)
            try:
                classNames.remove(be_deleted)
            except:
                pass
            old_set['choose'] = classNames
            with open('./settings/settings.json', encoding='utf-8', mode='w') as f:
                dump(old_set, f, ensure_ascii=False,)
            # 从储存的姓名列表去掉
            with open('./settings/name_sheet.json', encoding='utf-8') as f:
                old_set: dict = load(f)
                old_set.pop(be_deleted)
            with open('./settings/name_sheet.json', encoding='utf-8', mode='w') as f:
                dump(old_set, f, ensure_ascii=False,)
            # 刷新姓名列表，目的是去掉当前名单中可能出现的这些人
            getNames(outError=False)

    def clickName(self) -> None:
        """从左侧选栏之后把右侧的改过来"""
        # 允许编辑
        self.ui.NamesText.setEnabled(True)
        nowName = self.ui.listView.selectionModel().selectedIndexes()[0].data()
        if nowName == self.edit_class_name:  # 防止刚保存完就点自己
            return
        else:
            self.edit_class_name = nowName
        self.ui.NamesText.setPlainText(
            '\n'.join(self.all_name.get(self.edit_class_name)))

    def saveResult(self) -> None:
        """保存结果"""
        self.edit_class_name = self.ui.listView.selectionModel().selectedIndexes()[
            0].data()  # 班级名称
        with open('./settings/name_sheet.json', encoding='utf-8') as f:
            old_set: dict = load(f)
            old_set[self.edit_class_name] = self.ui.NamesText.toPlainText(
            ).strip().split('\n')
        with open('./settings/name_sheet.json', encoding='utf-8', mode='w') as f:
            dump(old_set, f, ensure_ascii=False)
        # 刷新姓名列表，目的是去掉当前名单中可能出现的这些人
        getNames(outError=False)
        QMessageBox.about(self.ui, '成功', f'保存“{self.edit_class_name}”成功')

    def textChanged(self) -> None:
        """右侧字符变化的时候"""
        if self.ui.NamesText.toPlainText().strip() == '':
            self.ui.PromptLabel.setText('请输入或粘贴名单')
        else:
            self.ui.PromptLabel.setText('正在编辑班级：{}，有{}个人'.format(
                self.edit_class_name, self.ui.NamesText.toPlainText().strip().count("\n")+1))


getNames()
main = MainWindow()
getNames(outError=False)
getIsLog()
if isLog:
    logger.add('.\日志\点名记录_{time:MM-DD HH-mm}（可删除）.log',
               format='<green>{time:MM-DD HH:mm:ss}</green>--<level>{message}</level>', rotation='1 day', retention='1 month')
ball.ui.toolButton.clicked.connect(main.changeThis)
apply_stylesheet(app, 'dark_teal.xml')
main.ui.show()
exit(app.exec_())
