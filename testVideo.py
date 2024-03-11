# -*- coding: utf-8 -*-
# 本程序用于图片、视频及摄像头中车牌识别与管理系统


from hyperlpr import *
# 导入OpenCV库
import cv2 as cv
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def drawRectBox(image, rect, addText, fontC):
    cv.rectangle(image, (int(round(rect[0])), int(round(rect[1]))),
                 (int(round(rect[2]) + 8), int(round(rect[3]) + 8)),
                 (0, 0, 255), 2)
    cv.rectangle(image, (int(rect[0] - 1), int(rect[1]) - 16), (int(rect[0] + 75), int(rect[1])), (0, 0, 255), -1,
                 cv.LINE_AA)
    img = Image.fromarray(image)
    draw = ImageDraw.Draw(img)
    draw.text((int(rect[0] + 1), int(rect[1] - 16)), addText, (255, 255, 255), font=fontC)
    imagex = np.array(img)
    return imagex


capture = cv.VideoCapture("./img/车牌检测.mp4")  # 读取视频文件
fontC = ImageFont.truetype("./Font/platech.ttf", 14, 0)  # 字体，用于标注图片

i = 1
while (True):
    ref, frame = capture.read()
    if ref:
        i = i + 1
        if i % 5 == 0:
            i = 0
            res_all = HyperLPR_plate_recognition(frame)  # 识别车牌
            if len(res_all) > 0:
                res, confi, axes = res_all[0]  # 获取结果
                frame = drawRectBox(frame, axes, res, fontC)
            cv.imshow("num", frame)  # 显示画面

        if cv.waitKey(1) & 0xFF == ord('q'):
            break  # 退出
    else:
        break
