# -*- coding: utf-8 -*-
"""
运行本项目需要安装的库：
    hyperlpr==0.0.2
    Keras==2.2.4
    tensorflow==1.13.1
    numpy==1.21.5
    Pillow==9.0.1
    PyQt5==5.15.4
    pyqt5-tools==5.15.4.3.2
    opencv-python==3.4.9.31
点击运行主程序runMain.py
"""
# 本程序用于图片、视频及摄像头中车牌识别与管理系统

import os
import warnings

from PlateRecognition import Plate_MainWindow
from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QMainWindow
# 忽略警告
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings(action='ignore')

if __name__ == '__main__':

    app = QApplication(argv)
    window = QMainWindow()
    ui = Plate_MainWindow(window)

    window.show()
    exit(app.exec_())
