from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QApplication,
                             QLabel, QFileDialog, QStyle, QVBoxLayout, QHBoxLayout, QListWidget,QGridLayout,
                             QListWidgetItem,QMenu,QAction, QSlider, QButtonGroup, QDialog,QComboBox
                             )

import sys,os, glob
from PyQt5.QtGui import QPalette, QColor
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.videofolder = ''
        self.videofolder = None
        self.labelfolder = None
        self.labelfiles = None
        self.setWindowTitle("Video Label Tool")
        self.videolist = Videolist(self)  # video menu
        self.videoplayer = VideoPlayer(self)
        self.labelBox = LabelBox(self)
        self._init_layout()
        self._createMenuBar()


    def _init_layout(self):
        self.resize(1000, 680)

        self.layout_main = QVBoxLayout()
        self.window = QWidget()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout_main)
        self.layout_top = QHBoxLayout()
        self.layout_top.addWidget(self.videoplayer, 8)
        self.layout_top.addWidget(self.videolist, 2)
        self.layout_main.addLayout(self.layout_top)
        self.layout_main.addWidget(self.labelBox)
        self.setLayout(self.layout_main)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

        action_videodir = QAction("set video path", self)
        action_videodir.triggered.connect(self._setVideoDir)
        action_labeldir = QAction("set label path", self)
        action_labeldir.triggered.connect(self._setLabelDir)

        fileMenu.addAction(action_videodir)
        fileMenu.addAction(action_labeldir)

    def _setVideoDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select video Directory"))
        self.videolist._set_files(folder)
        self.videofolder = folder
        print(self.videofolder)

    def _setLabelDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select label Directory"))
        if folder == '':
            return
        self.labelfolder = folder
        extension = 'txt'
        self.labelfiles = os.listdir(folder)
        for fn in self.labelfiles:
            if not fn.endswith(extension):
                self.labelfiles.remove(fn)
        print(self.labelfolder)


class Videolist(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.folder = parent.videofolder
        self.resize(100, 480)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('green'))
        self.setPalette(palette)
        self.setStyleSheet('font-size: 14px;')


    def _set_files(self, folder):
        if folder == '':
            return
        self.folder = folder
        extension = tuple(['mp4', 'avi'])

        filenames = os.listdir(folder)
        for fn in filenames:
            if not fn.endswith(extension):
                filenames.remove(fn)
        self.addItems(filenames)
        self.itemDoubleClicked.connect(self._getItem)


    def _getItem(self, item):
        print(item.text())
        self.parent.videoplayer.openFile(os.path.join(self.folder,item.text()))
        self.parent.labelBox.cleanLabelBox()
        self.parent.labelBox.cleanSavedlabels()
        self.parent.labelBox.choices.setCurrentIndex(0)
        self.parent.labelBox.getLableFile(item.text())

class LabelBox(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.currentlabels = {}
        self.labelrules = {}
        self._init_labelbox()


    def _init_labelbox(self):
        with open('preference_classes.txt', 'r') as f:
            labels = f.read().splitlines()
        self.setStyleSheet('font-size: 15px;')
        self.buttongroup = QButtonGroup()
        self.buttongroup.buttonClicked.connect(self.selected)
        self.number = int(labels[0])
        self.choices = QComboBox()
        self.choices.addItems(list(map(str,range(1,self.number+1))))
        self.choices.currentIndexChanged.connect(self.choiceChange)

        self.layout.addWidget(self.choices)
        self.labelamount = 0
        for li, l in enumerate(labels[1:]):
            self.labelrules[l] = li
            self.label = QPushButton(l, self)
            self.label.setCheckable(True)
            self.layout.addWidget(self.label, 1)
            self.buttongroup.addButton(self.label, li)
            self.labelamount += 1
        self.buttongroup.setExclusive(False)
        self.cleanSavedlabels()

    def warning(self, case):
        dlg = QDialog(self)
        dlg.setWindowTitle("Tip")
        dlg.exec()

    def choiceChange(self, i):
        for xi, x in enumerate(self.currentlabels[self.choices.itemText(i)]):
            self.buttongroup.button(xi).setChecked(bool(x))

    def selected(self, button):
        buttonindex = self.labelrules[button.text()]
        if self.parent.labelfiles is None:
            button.setChecked(False)
            dlg = QDialog(self)
            dlg.setWindowTitle("Please click FILE to set label folder!")
            dlg.exec()
        else:
            videopath = self.parent.videoplayer.videopath
            if videopath is None:
                dlg = QDialog(self)
                dlg.setWindowTitle("Please pick a VIDEO from left list!")
                dlg.exec()
            videoname = os.path.basename(videopath)

            if self.parent.labelfolder is not None:
                labelpath = os.path.join(self.parent.labelfolder, videoname)
                labelid = self.choices.currentText()
                self.currentlabels[labelid][buttonindex] = int(button.isChecked())
                self.createLabelFile(labelpath)

            else:
                dlg = QDialog(self)
                dlg.setWindowTitle("Please click FILE to set label folder!")
                dlg.exec()


    def getLableFile(self, videoname):
        fpath = os.path.join(self.parent.labelfolder, videoname.replace('mp4','txt'))
        print('getLableFile: ', fpath)
        if os.path.isfile(fpath):
            with open(fpath,'r') as f:
               label_lines = f.read().splitlines()
               for li, labelline in enumerate(label_lines):
                   labels = labelline.split(' ')
                   for ii, label in enumerate(labels[1:]):
                       self.currentlabels[labels[0]][ii] = int(label)
            for curr_i, curr_label in enumerate(self.currentlabels[self.choices.currentText()]):
                self.buttongroup.button(curr_i).setChecked(bool(int(curr_label)))
        else:
            self.cleanLabelBox()
            self.cleanSavedlabels()
        print(self.currentlabels)

    def createLabelFile(self, fpath):
        fpath = fpath.replace('mp4','txt')
        print('createLabelFile: ', fpath)
        with open(fpath,'w') as f:
            for id in self.currentlabels.keys():
                f.write(id + ' ' + (' ').join(map(str,self.currentlabels[id])) +'\n')
                print(self.currentlabels[id])

    def cleanLabelBox(self):
        for bnt_i, bnt in enumerate(self.buttongroup.buttons()):
            self.buttongroup.button(bnt_i).setChecked(False)

    def cleanSavedlabels(self):
        for n in range(1,self.number+1):
            self.currentlabels[str(n)] = self.labelamount*[0]

class VideoPlayer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = QVideoWidget()
        self.playButton = QPushButton()
        self.videopath = None

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        layout.addWidget(self.slider)
        layout.addWidget(self.playButton)

        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        self.setLayout(layout)
        self.mediaPlayer.setVideoOutput(self.videoWidget)


    def openFile(self, fileName):
        if fileName != '':
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.videopath = fileName
            self.mediaPlayer.play()


    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def position_changed(self, position):
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)


app = QApplication(sys.argv)
mainwindow = MainWindow()
mainwindow.show()
sys.exit(app.exec_())