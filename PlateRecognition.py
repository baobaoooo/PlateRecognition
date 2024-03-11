# -*- coding: utf-8 -*-
# 本程序用于图片、视频及摄像头中车牌识别与管理系统


import os
import warnings
from os import getcwd
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from hyperlpr import HyperLPR_plate_recognition
from PlateRecognition_UI import Ui_MainWindow

# 忽略警告
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings(action='ignore')


class Plate_MainWindow(Ui_MainWindow):
    def __init__(self, MainWindow):
        self.count = 0  # 表格行数，用于记录识别车牌条目
        self.res_set = []  # 用于车牌历史结果记录的列表

        self.cap_video = None  # 视频流对象

        self.path = getcwd()
        self.video_path = getcwd()
        self.fontC = ImageFont.truetype("D:\Learn\物联网工程专业\物联网系统设计+matlab\PlateRecognition\GOTHIC.TTF", 14, 0)

        self.timer_camera = QtCore.QTimer()  # 定时器
        self.timer_video = QtCore.QTimer()  # 视频定时器
        self.flag_timer = ""  # 用于标记正在进行的功能项（视频/摄像）

        self.CAM_NUM = 0  # 摄像头标号
        self.cap = cv2.VideoCapture(self.CAM_NUM)  # 屏幕画面对象
        self.cap_video = None  # 视频流对象
        # self.model = pr.LPR("./HyperLPR_CarNum/model/cascade_lbp.xml", "./HyperLPR_CarNum/model/model12.h5",
        #                     "./HyperLPR_CarNum/model/ocr_plate_all_gru.h5")

        self.current_image = None  # 保存的画面
        self.setupUi(MainWindow)  # 界面生成
        self.retranslateUi(MainWindow)  # 界面控件
        # 设置表格形式
        self.tableWidget.setColumnWidth(0, 80)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 150)
        self.tableWidget.setColumnWidth(3, 200)
        self.tableWidget.setColumnWidth(4, 120)
        # self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.slot_init()  # 槽函数设置

    def slot_init(self):
        self.toolButton_file.clicked.connect(self.choose_file)
        self.toolButton_runing.clicked.connect(self.run_rec)
        self.toolButton_camera.clicked.connect(self.button_open_camera_click)
        self.tableWidget.cellPressed.connect(self.table_review)
        self.toolButton_video.clicked.connect(self.button_open_video_click)
        self.timer_video.timeout.connect(self.show_video)
        self.timer_camera.timeout.connect(self.show_camera)
        self.toolButton_model.clicked.connect(self.choose_folder)

    def table_review(self, row, col):
        try:
            if col == 0:  # 点击第一列时
                this_path = self.tableWidget.item(row, 1)  # 表格中的文件路径
                res = self.tableWidget.item(row, 2)  # 表格中记录的识别结果
                axes = self.tableWidget.item(row, 3)  # 表格中记录的坐标

                if (this_path is not None) & (res is not None) & (axes is not None):
                    this_path = this_path.text()
                    if os.path.exists(this_path):
                        res = res.text()
                        axes = axes.text()

                        image = self.cv_imread(this_path)  # 读取选择的图片
                        image = cv2.resize(image, (500, 500))  # 设定图像尺寸为显示界面大小

                        axes = [int(i) for i in axes.split(",")]
                        confi = float(self.tableWidget.item(row, 4).text())

                        image = self.drawRectBox(image, axes, res)
                        # 在Qt界面中显示检测完成画面
                        show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                        self.label_display.setPixmap(QtGui.QPixmap.fromImage(showImage))
                        self.label_display.setScaledContents(True)

                        # 在界面标签中显示结果
                        self.label_score_result.setText(str(round(confi * 100, 2)) + "%")
                        self.label_score_x1.setText(str(int(axes[0])))
                        self.label_score_y1.setText(str(int(axes[1])))
                        self.label_score_x2.setText(str(int(axes[2])))
                        self.label_score_y2.setText(str(int(axes[3])))
                        self.label_plate_result.setText(str(res))
                        QtWidgets.QApplication.processEvents()
        except:
            self.label_display.setText('重现车牌记录时出错，请检查表格内容！')
            self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

    def choose_file(self):
        self.flag_timer = ""

        # 选择图片或视频文件后执行此槽函数
        self.timer_camera.stop()
        self.timer_video.stop()
        if self.cap:
            self.cap.release()
        if self.cap_video:
            self.cap_video.release()  # 释放视频画面帧

        # 清除UI上的label显示
        self.label_plate_result.setText("省X00000")
        self.label_score_result.setText("0")
        self.label_score_x1.setText("0")
        self.label_score_x2.setText("0")
        self.label_score_y1.setText("0")
        self.label_score_y2.setText("0")

        # 清除文本框的显示内容
        self.textEdit_model.setText("请选择文件夹")
        self.textEdit_model.setStyleSheet("background-color: transparent;\n"
                                          "border-color: rgb(0, 170, 255);\n"
                                          "color: rgb(0, 170, 255);\n"
                                          "font: regular 12pt \"华为仿宋\";")
        self.textEdit_camera.setText("实时摄像已关闭")
        self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                           "border-color: rgb(0, 170, 255);\n"
                                           "color: rgb(0, 170, 255);\n"
                                           "font: regular 12pt \"华为仿宋\";")
        self.textEdit_video.setText('实时视频已关闭')
        self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                          "border-color: rgb(0, 170, 255);\n"
                                          "color: rgb(0, 170, 255);\n"
                                          "font: regular 12pt \"华为仿宋\";")
        self.label_display.clear()
        self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

        # 使用文件选择对话框选择图片
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            self.centralwidget, "选取图片文件",
            self.path,  # 起始路径
            "图片(*.jpg;*.jpeg;*.png)")  # 文件类型
        self.path = fileName_choose  # 保存路径
        if self.path != '':
            self.flag_timer = "image"
            self.textEdit_file.setText(self.path + '文件已选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            image = self.cv_imread(self.path)  # 读取选择的图片
            # image = cv2.imread("../LicensePlateRecognition/test3.jpeg")  # 读取选择的图片

            image = cv2.resize(image, (500, 500))  # 设定图像尺寸为显示界面大小

            if len(image.shape) < 3:
                self.path = ''
                self.label_display.setText("需要正常彩色图片，请重新选择！")
                self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

                return

            self.current_image = image.copy()
            show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # show = image.copy()
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            a = QtGui.QPixmap.fromImage(showImage)
            # a = a.scaled(self.label_display.size().width(), self.label_display.size().height(),
            # aspectRatioMode=Qt.KeepAspectRatio)
            self.label_display.setPixmap(a)
            self.label_display.setScaledContents(True)
            QtWidgets.QApplication.processEvents()

        else:
            # 选择取消，恢复界面状态
            self.flag_timer = ""
            self.textEdit_file.setText('图片文件未选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")

    def do_choose_file(self):
        if self.path != '':
            self.label_display.clear()
            QtWidgets.QApplication.processEvents()
            image = self.cv_imread(self.path)  # 读取选择的图片

            image = cv2.resize(image, (500, 500))  # 设定图像尺寸为显示界面大小

            # self.current_image = image.copy()
            # 生成模型对象
            res_all = HyperLPR_plate_recognition(image)
            # res_all = self.model.SimpleRecognizePlateByE2E(image)
            if len(res_all) > 0:
                res, confi, axes = res_all[0]

                image = self.drawRectBox(image, axes, res)

                # 在Qt界面中显示检测完成画面
                show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                self.label_display.setPixmap(QtGui.QPixmap.fromImage(showImage))
                self.label_display.setScaledContents(True)

                # 在界面标签中显示结果
                self.label_score_result.setText(str(round(confi * 100, 2)) + "%")
                self.label_score_x1.setText(str(int(axes[0])))
                self.label_score_y1.setText(str(int(axes[1])))
                self.label_score_x2.setText(str(int(axes[2])))
                self.label_score_y2.setText(str(int(axes[3])))
                self.label_plate_result.setText(str(res))
                QtWidgets.QApplication.processEvents()

                # 将结果记录至列表中
                self.res_set.append(res_all[0])
                self.change_table(self.path, res, axes, confi)

            else:
                self.label_display.setText('未能检测到车牌，请重新选择！')
                self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

        else:
            self.flag_timer = ""
            self.textEdit_file.setText('图片文件未选中或不符合！')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")

    def choose_folder(self):
        # 选择图片或视频文件后执行此槽函数
        self.timer_camera.stop()
        self.timer_video.stop()
        if self.cap:
            self.cap.release()
        if self.cap_video:
            self.cap_video.release()  # 释放视频画面帧
        # 清除UI上的label显示
        self.label_plate_result.setText("省X00000")
        self.label_score_result.setText("0")
        self.label_score_x1.setText("0")
        self.label_score_x2.setText("0")
        self.label_score_y1.setText("0")
        self.label_score_y2.setText("0")

        # 清除文本框的显示内容
        self.textEdit_file.setText("选择车牌图片文件")
        self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                         "border-color: rgb(0, 170, 255);\n"
                                         "color: rgb(0, 170, 255);\n"
                                         "font: regular 12pt \"华为仿宋\";")
        self.textEdit_camera.setText("实时摄像已关闭")
        self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                           "border-color: rgb(0, 170, 255);\n"
                                           "color: rgb(0, 170, 255);\n"
                                           "font: regular 12pt \"华为仿宋\";")
        self.textEdit_video.setText('实时视频已关闭')
        self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                          "border-color: rgb(0, 170, 255);\n"
                                          "color: rgb(0, 170, 255);\n"
                                          "font: regular 12pt \"华为仿宋\";")
        self.label_display.clear()
        self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")
        # 选择文件夹
        dir_choose = QFileDialog.getExistingDirectory(self.centralwidget, "选取文件夹", self.path)
        self.path = dir_choose  # 保存路径

        if dir_choose != "":
            self.textEdit_model.setText(dir_choose + '文件夹已选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            self.flag_timer = "folder"

        else:
            # 选择取消，恢复界面状态
            self.flag_timer = ""
            self.textEdit_model.setText('文件夹未选中')
            self.textEdit_model.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")

    def do_choose_folder(self):
        rootdir = os.path.join(self.path)
        for (dirpath, dirnames, filenames) in os.walk(rootdir):
            for filename in filenames:
                temp_type = os.path.splitext(filename)[1]
                if temp_type == '.png' or temp_type == '.jpg' or temp_type == '.jpeg':

                    img_path = dirpath + '/' + filename

                    image = self.cv_imread(img_path)  # 读取选择的图片
                    image = cv2.resize(image, (500, 500))  # 设定图像尺寸为显示界面大小

                    # 生成模型对象
                    res_all = HyperLPR_plate_recognition(image)
                    # res_all = self.model.SimpleRecognizePlateByE2E(image)
                    if len(res_all) > 0:
                        res, confi, axes = res_all[0]

                        image = self.drawRectBox(image, axes, res)

                        # 在Qt界面中显示检测完成画面
                        show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                        self.label_display.setPixmap(QtGui.QPixmap.fromImage(showImage))
                        self.label_display.setScaledContents(True)
                        QtWidgets.QApplication.processEvents()

                        # 在界面标签中显示结果
                        self.label_score_result.setText(str(round(confi * 100, 2)) + "%")
                        self.label_score_x1.setText(str(int(axes[0])))
                        self.label_score_y1.setText(str(int(axes[1])))
                        self.label_score_x2.setText(str(int(axes[2])))
                        self.label_score_y2.setText(str(int(axes[3])))
                        self.label_plate_result.setText(str(res))
                        QtWidgets.QApplication.processEvents()

                        # 将结果记录至列表中
                        self.res_set.append(res_all[0])
                        self.change_table(img_path, res, axes, confi)

                    else:
                        self.label_display.setText('未能检测到车牌，请重新选择！')
                        self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

    def change_table(self, path, res, axes, confi):
        # 更新表格记录
        self.count += 1  # 每识别出结果增加一条记录
        if self.count > 6:
            self.tableWidget.setRowCount(self.count)
        newItem = QTableWidgetItem(str(self.count))  # 在表格中记录序号
        newItem.setTextAlignment(Qt.AlignCenter)
        self.tableWidget.setItem(self.count - 1, 0, newItem)

        newItem = QTableWidgetItem(path)  # 在表格中记录车牌路径
        newItem.setTextAlignment(Qt.AlignVCenter)
        self.tableWidget.setItem(self.count - 1, 1, newItem)

        newItem = QTableWidgetItem(res)  # 记录识别出的车牌在表格中
        newItem.setTextAlignment(Qt.AlignCenter)
        self.tableWidget.setItem(self.count - 1, 2, newItem)
        self.tableWidget.setCurrentItem(newItem)

        str_axes = str(axes[0]) + "," + str(axes[1]) + "," + str(axes[2]) + "," + str(axes[3])
        newItem = QTableWidgetItem(str_axes)  # 记录识别出的车牌位置在表格中
        newItem.setTextAlignment(Qt.AlignCenter)
        self.tableWidget.setItem(self.count - 1, 3, newItem)
        self.tableWidget.setCurrentItem(newItem)

        newItem = QTableWidgetItem(str(round(confi, 4)))  # 记录识别出的车牌置信度在表格中
        newItem.setTextAlignment(Qt.AlignCenter)
        self.tableWidget.setItem(self.count - 1, 4, newItem)
        self.tableWidget.setCurrentItem(newItem)

    def button_open_camera_click(self):
        self.count = 0
        self.res_set = []
        if self.timer_video.isActive():
            self.timer_video.stop()
        self.flag_timer = ""
        if self.cap:
            self.cap.release()
        if self.cap_video:
            self.cap_video.release()  # 释放视频画面帧

        if not self.timer_camera.isActive():  # 检查定时状态
            flag = self.cap.open(self.CAM_NUM)  # 检查相机状态
            if not flag:  # 相机打开失败提示
                msg = QtWidgets.QMessageBox.warning(self.centralwidget, u"Warning",
                                                    u"请检测相机与电脑是否连接正确！ ",
                                                    buttons=QtWidgets.QMessageBox.Ok,
                                                    defaultButton=QtWidgets.QMessageBox.Ok)
                self.flag_timer = ""
            else:
                self.textEdit_camera.setText("相机准备就绪")
                self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                                   "border-color: rgb(0, 170, 255);\n"
                                                   "color: rgb(0, 170, 255);\n"
                                                   "font: regular 12pt \"华为仿宋\";")
                # 准备运行识别程序
                self.flag_timer = "camera"
                # 清除文本框的显示内容
                self.textEdit_model.setText("请选择文件夹")
                self.textEdit_model.setStyleSheet("background-color: transparent;\n"
                                                  "border-color: rgb(0, 170, 255);\n"
                                                  "color: rgb(0, 170, 255);\n"
                                                  "font: regular 12pt \"华为仿宋\";")
                self.textEdit_video.setText("实时视频已关闭")
                self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                                  "border-color: rgb(0, 170, 255);\n"
                                                  "color: rgb(0, 170, 255);\n"
                                                  "font: regular 12pt \"华为仿宋\";")
                self.textEdit_file.setText('图片文件未选中')
                self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                                 "border-color: rgb(0, 170, 255);\n"
                                                 "color: rgb(0, 170, 255);\n"
                                                 "font: regular 12pt \"华为仿宋\";")
                # self.label_display.setText('正在启动识别系统...\n\nleading')
                QtWidgets.QApplication.processEvents()

                # 清除UI上的label显示
                self.label_plate_result.setText("省X00000")
                self.label_score_result.setText("0")
                self.label_score_x1.setText("0")
                self.label_score_x2.setText("0")
                self.label_score_y1.setText("0")
                self.label_score_y2.setText("0")

        else:
            # 定时器未开启，界面回复初始状态
            self.flag_timer = ""
            self.timer_camera.stop()
            if self.cap:
                self.cap.release()
            self.label_display.clear()
            self.textEdit_file.setText('文件未选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            self.textEdit_camera.setText('实时摄像已关闭')
            self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                               "border-color: rgb(0, 170, 255);\n"
                                               "color: rgb(0, 170, 255);\n"
                                               "font: regular 12pt \"华为仿宋\";")
            self.textEdit_video.setText('实时视频已关闭')
            self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                              "border-color: rgb(0, 170, 255);\n"
                                              "color: rgb(0, 170, 255);\n"
                                              "font: regular 12pt \"华为仿宋\";")
            self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")
            # 清除UI上的label显示
            self.label_plate_result.setText("省X00000")
            self.label_score_result.setText("0")
            self.label_score_x1.setText("0")
            self.label_score_x2.setText("0")
            self.label_score_y1.setText("0")
            self.label_score_y2.setText("0")

    def show_camera(self):
        # 定时器槽函数，每隔一段时间执行
        flag, image = self.cap.read()  # 获取画面
        if flag:
            # image = cv2.flip(image, 1)  # 左右翻转
            self.current_image = image.copy()

            res_all = HyperLPR_plate_recognition(image)
            if len(res_all) > 0:
                res, confi, axes = res_all[0]
                # axes[2] = axes[0] + axes[2]
                # axes[3] = axes[1] + axes[3]

                image = self.drawRectBox(image, axes, res)

                # 在界面标签中显示结果
                self.label_score_result.setText(str(round(confi * 100, 2)) + "%")
                self.label_score_x1.setText(str(int(axes[0])))
                self.label_score_y1.setText(str(int(axes[1])))
                self.label_score_x2.setText(str(int(axes[2])))
                self.label_score_y2.setText(str(int(axes[3])))
                self.label_plate_result.setText(str(res))
                QtWidgets.QApplication.processEvents()

                # 将结果记录至列表中
                if res not in self.res_set:
                    self.res_set.append(res)
                    self.change_table(str(self.count), res, axes, confi)

            else:
                # 清除UI上的label显示
                self.label_plate_result.setText("省X00000")
                self.label_score_result.setText("0")
                self.label_score_x1.setText("0")
                self.label_score_x2.setText("0")
                self.label_score_y1.setText("0")
                self.label_score_y2.setText("0")

            # 在Qt界面中显示检测完成画面
            show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_display.setPixmap(QtGui.QPixmap.fromImage(showImage))
            self.label_display.setScaledContents(True)

    def button_open_video_click(self):
        self.count = 0
        self.res_set = []
        self.tableWidget.clearContents()
        if self.timer_camera.isActive():
            self.timer_camera.stop()
        if self.cap:
            self.cap.release()
        if self.cap_video:
            self.cap_video.release()  # 释放视频画面帧
        self.label_display.clear()
        self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")

        self.flag_timer = ""
        if not self.timer_video.isActive():  # 检查定时状态
            # 弹出文件选择框选择视频文件
            fileName_choose, filetype = QFileDialog.getOpenFileName(self.centralwidget, "选取视频文件",
                                                                    self.video_path,  # 起始路径
                                                                    "视频(*.mp4;*.avi)")  # 文件类型
            self.video_path = fileName_choose
            if fileName_choose != '':
                self.flag_timer = "video"
                self.textEdit_video.setText(fileName_choose + '文件已选中')
                self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                                  "border-color: rgb(0, 170, 255);\n"
                                                  "color: rgb(0, 170, 255);\n"
                                                  "font: regular 12pt \"华为仿宋\";")
                # self.label_display.setText('正在启动识别系统...\n\nleading')
                QtWidgets.QApplication.processEvents()

                try:  # 初始化视频流
                    self.cap_video = cv2.VideoCapture(fileName_choose)
                except:
                    print("[INFO] could not determine # of frames in video")
            else:
                self.textEdit_video.setText('视频文件未选中')
            # 清除文本框的显示内容
            self.textEdit_model.setText("选择图片文件夹")
            self.textEdit_model.setStyleSheet("background-color: transparent;\n"
                                              "border-color: rgb(0, 170, 255);\n"
                                              "color: rgb(0, 170, 255);\n"
                                              "font: regular 12pt \"华为仿宋\";")
            self.textEdit_camera.setText("实时摄像已关闭")
            self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                               "border-color: rgb(0, 170, 255);\n"
                                               "color: rgb(0, 170, 255);\n"
                                               "font: regular 12pt \"华为仿宋\";")
            self.textEdit_file.setText('图片文件未选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            # self.label_display.setText('正在启动识别系统...\n\nleading')
            QtWidgets.QApplication.processEvents()

            # 清除UI上的label显示
            self.label_plate_result.setText("省X00000")
            self.label_score_result.setText("0")
            self.label_score_x1.setText("0")
            self.label_score_x2.setText("0")
            self.label_score_y1.setText("0")
            self.label_score_y2.setText("0")

        else:
            # 定时器已开启，界面回复初始状态
            self.flag_timer = ""
            self.timer_video.stop()
            if self.cap:
                self.cap.release()
            self.label_display.clear()
            self.textEdit_file.setText('图片文件未选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            self.textEdit_camera.setText('实时摄像已关闭')
            self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                               "border-color: rgb(0, 170, 255);\n"
                                               "color: rgb(0, 170, 255);\n"
                                               "font: regular 12pt \"华为仿宋\";")
            self.textEdit_video.setText('实时视频已关闭')
            self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                              "border-color: rgb(0, 170, 255);\n"
                                              "color: rgb(0, 170, 255);\n"
                                              "font: regular 12pt \"华为仿宋\";")
            self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")
            # 清除UI上的label显示
            self.label_plate_result.setText("省X00000")
            self.label_score_result.setText("0")
            self.label_score_x1.setText("0")
            self.label_score_x2.setText("0")
            self.label_score_y1.setText("0")
            self.label_score_y2.setText("0")

    def show_video(self):
        # 定时器槽函数，每隔一段时间执行
        flag, image = self.cap_video.read()  # 获取画面
        if flag:
            # 使用模型预测
            image = cv2.resize(image, (500, 500))  # 设定图像尺寸为显示界面大小

            res_all = HyperLPR_plate_recognition(image)
            if len(res_all) > 0:
                res, confi, axes = res_all[0]
                # axes[2] = axes[0] + axes[2]
                # axes[3] = axes[1] + axes[3]

                image = self.drawRectBox(image, axes, res)

                # 在界面标签中显示结果
                self.label_score_result.setText(str(round(confi * 100, 2)) + "%")
                self.label_score_x1.setText(str(int(axes[0])))
                self.label_score_y1.setText(str(int(axes[1])))
                self.label_score_x2.setText(str(int(axes[2])))
                self.label_score_y2.setText(str(int(axes[3])))
                self.label_plate_result.setText(str(res))
                QtWidgets.QApplication.processEvents()

                # 将结果记录至列表中
                if res not in self.res_set:
                    self.res_set.append(res)
                    self.change_table(str(self.count), res, axes, confi)

            else:
                # 清除UI上的label显示
                self.label_plate_result.setText("省X00000")
                self.label_score_result.setText("0")
                self.label_score_x1.setText("0")
                self.label_score_x2.setText("0")
                self.label_score_y1.setText("0")
                self.label_score_y2.setText("0")

            # 在Qt界面中显示检测完成画面
            show = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_display.setPixmap(QtGui.QPixmap.fromImage(showImage))
            self.label_display.setScaledContents(True)

    def run_rec(self):

        if self.flag_timer == "image":
            self.do_choose_file()

        elif self.flag_timer == "video":
            if not self.timer_video.isActive():
                # self.count = 0
                # self.tableWidget.clearContents()
                # 打开定时器
                self.timer_video.start(30)
            else:
                self.timer_video.stop()

        elif self.flag_timer == "folder":
            self.count = 0
            self.tableWidget.clearContents()
            QtWidgets.QApplication.processEvents()
            self.do_choose_folder()

        elif self.flag_timer == "camera":
            if not self.timer_camera.isActive():
                self.count = 0
                self.tableWidget.clearContents()
                QtWidgets.QApplication.processEvents()
                self.timer_camera.start(30)
            else:
                self.timer_camera.stop()
                self.flag_timer = ""
                if self.cap:
                    self.cap.release()
                self.textEdit_camera.setText("实时摄像已关闭")
                self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                                   "border-color: rgb(0, 170, 255);\n"
                                                   "color: rgb(0, 170, 255);\n"
                                                   "font: regular 12pt \"华为仿宋\";")
                QtWidgets.QApplication.processEvents()

        else:
            self.textEdit_model.setText('选择图片文件夹')
            self.textEdit_model.setStyleSheet("background-color: transparent;\n"
                                              "border-color: rgb(0, 170, 255);\n"
                                              "color: rgb(0, 170, 255);\n"
                                              "font: regular 12pt \"华为仿宋\";")
            self.textEdit_file.setText('图片文件未选中')
            self.textEdit_file.setStyleSheet("background-color: transparent;\n"
                                             "border-color: rgb(0, 170, 255);\n"
                                             "color: rgb(0, 170, 255);\n"
                                             "font: regular 12pt \"华为仿宋\";")
            self.textEdit_camera.setText("实时摄像已关闭")
            self.textEdit_camera.setStyleSheet("background-color: transparent;\n"
                                               "border-color: rgb(0, 170, 255);\n"
                                               "color: rgb(0, 170, 255);\n"
                                               "font: regular 12pt \"华为仿宋\";")
            # self.textEdit_model
            self.textEdit_video.setText('实时视频已关闭')
            self.textEdit_video.setStyleSheet("background-color: transparent;\n"
                                              "border-color: rgb(0, 170, 255);\n"
                                              "color: rgb(0, 170, 255);\n"
                                              "font: regular 12pt \"华为仿宋\";")
            self.label_display.clear()
            self.label_display.setStyleSheet("border-image: url(:/newPrefix/images_test/ini-image.png);")
            self.count = 0
            self.tableWidget.clearContents()
            # 清除UI上的label显示
            self.label_plate_result.setText("省X00000")
            self.label_score_result.setText("0")
            self.label_score_x1.setText("0")
            self.label_score_x2.setText("0")
            self.label_score_y1.setText("0")
            self.label_score_y2.setText("0")

    def drawRectBox(self, image, rect, addText):
        cv2.rectangle(image, (int(round(rect[0])), int(round(rect[1]))),
                      (int(round(rect[2]) + 8), int(round(rect[3]) + 8)),
                      (0, 0, 255), 2)
        cv2.rectangle(image, (int(rect[0] - 1), int(rect[1]) - 16), (int(rect[0] + 75), int(rect[1])), (0, 0, 255), -1,
                      cv2.LINE_AA)
        img = Image.fromarray(image)
        draw = ImageDraw.Draw(img)
        draw.text((int(rect[0] + 1), int(rect[1] - 16)), addText, (255, 255, 255), font=self.fontC)
        imagex = np.array(img)
        return imagex

    def cv_imread(self, filePath):
        # 读取图片
        # cv_img = cv2.imread(filePath)
        cv_img = cv2.imdecode(np.fromfile(filePath, dtype=np.uint8), -1)
        # imdecode读取的是rgb，如果后续需要opencv处理的话，需要转换成bgr，转换后图片颜色会变化
        # cv_img = cv2.cvtColor(cv_img,cv2.COLOR_RGB2BGR)
        if len(cv_img.shape) > 2:
            if cv_img.shape[2] > 3:
                cv_img = cv_img[:, :, :3]
        return cv_img
