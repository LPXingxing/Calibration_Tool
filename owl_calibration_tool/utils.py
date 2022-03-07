import os
import datetime
import time
import math
import cv2
import numpy as np
import configparser


def parser_config_file(session,key):
    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")
    return config.get(session,key)


def validateTitle(title):
    for word in title:
        if (ord(word) < 48 or ord(word) > 57) and word !=".":
            title = title.replace(word, '~')
    return title


def transfer_to_16_bit_data(data):
    if "0x" in data:
        regValue = int(data.strip(), 16)
    else:
        regValue = int(data.strip())
    return regValue


def get_now_million_second():
    return math.modf(time.time() * 1000)[1]


def get_now_second_time():
    return time.strftime("%Y%m%d%H%M%S",time.localtime())


def check_result_ok(test_result,dict_test_project):
    result_ok=[]
    for i in range(len(dict_test_project)):
        dict_test_project[i]=validateTitle(dict_test_project[i])
        if "~" in dict_test_project[i]:
            min_data=dict_test_project[i].split("~")[0]
            max_data=dict_test_project[i].split("~")[1]
            if test_result[i]>=float(min_data) and test_result[i]<=float(max_data):
                result_ok.append("✓")
            else:
                result_ok.append("X")
    print(result_ok)
    return result_ok


def concat_list_info(concat_list):
    concat_str=""
    for index in concat_list:
        concat_str+=str(index)+","
    return concat_str.strip().rstrip(",")


def bgr2gray(img):
    gray=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray


def gaussblur(img, kernel=(5, 5), sigma=0):
    dst = cv2.GaussianBlur(img, kernel, sigma)
    return dst


def threshold(img):
    # dst=cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,801,1)
    ret, dst = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return dst


def morphological_operation(binary_img):
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (75, 75))
    dst_open = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel=kernel)
    kernel2 = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    dst_close = cv2.morphologyEx(dst_open, cv2.MORPH_CLOSE, kernel=kernel2)

    return dst_close


def re_img(img):
    img_r = 255 - img
    return img_r


def findcounters(img):
    contuors, heriachy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contuors


def drawcounters(img, contours):
    dst = cv2.drawContours(img, contours, -1, (0, 0, 255), 20)
    return dst


def drawbox(img, counters):
    for i in range(len(counters)):
        area = cv2.contourArea(counters[i])

        if area>0 and area<1000:
            x, y, w, h = cv2.boundingRect(counters[i])
            print("No.%d,area=%d"%(i,area))
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return img


def get_Several_MinMax_Array(np_arr, several):
    """
    获取numpy数值中最大或最小的几个数
    :param np_arr:  numpy数组
    :param several: 最大或最小的个数（负数代表求最大，正数代表求最小）
    :return:
        several_min_or_max: 结果数组
    """
    if several > 0:
        several_min_or_max = np_arr[np.argpartition(np_arr,several)[:several]]
    else:
        #print("cal minnnnnnnnnnnn")
        several_min_or_max = np_arr[np.argpartition(np_arr, several)[several:]]
    return several_min_or_max





