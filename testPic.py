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
    image = np.array(img)
    return image


image = cv.imread('./img/test.jpeg')  # 读取选择的图片
res_all = HyperLPR_plate_recognition(image)
# fontC = ImageFont.truetype("D:\Learn\物联网工程专业\物联网系统设计+matlab\PlateRecognition\GOTHIC.TTF", 14, 0)
fontC = ImageFont.truetype("C:/Users\liu\Desktop/find_work\PlateRecognition\GOTHIC.TTF", 14, 0)
res, confi, axes = res_all[0]
image = drawRectBox(image, axes, res, fontC)
cv.imshow('Stream', image)
c = cv.waitKey(0) & 0xff
