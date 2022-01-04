import sys, time
import os
from glob import glob
from PyQt5 import QtWidgets, QtGui,QtCore
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QListWidgetItem,QListWidget,QWidget,QListView,QHBoxLayout,QMenu,QAction
from PyQt5.QtCore import QDir, QTimer, QThread, pyqtSignal, Qt,QSize
from PyQt5.QtGui import QPixmap, QImage
from ui_mainwindow import Ui_MainWindow
import threading
import cv2
import numpy as np
import glob
from PIL import Image
import configparser
import binascii
import subprocess
import struct
from PIL import ImageQt
from argusCamera import ArgusCamera, ArgusStrOverlay, ArgusRectOverlay
dict_right_calibrate_pic_error={}
dict_left_calibrate_pic_error={}
FLAG=False
CAPTURE_FLAG=False
RIGHT_CAPTURE_FLAG=False


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

    def window_init(self):
        self.ch=IconListWidget()
        self.ch.show()
        self.device_name=self.parser_config_file("device","device_name")
        self.soft_ware__name="Stereo calibrate tool_%s_V2.0"%self.device_name
        self.setWindowTitle(self.soft_ware__name)
        self.setFixedSize(820, 740)
        self.capture_num=0
        self.old_sn_number=""
        self.pushButton_2.clicked.connect(self.capture_image)
        self.pushButton_3.clicked.connect(self.calibration)
        self.pushButton_4.clicked.connect(self.download_eeprom_data_process)
        self.pushButton_5.clicked.connect(self.update_eeprom_data_process)
        self.pushButton_6.clicked.connect(self.imu_data_write_process)

        self.vertify_Button.clicked.connect(self.vertify_calibrate_process)

        #self.sn_number=self.lineEdit.text()
        #print(self.sn_number)
        '''
        gst_str_video0 = ('nvarguscamerasrc  sensor-id=0 ! '
                          'video/x-raw(memory:NVMM), '
                          'width=(int)1920, height=(int)1200, '
                          'format=(string)NV12, framerate=(fraction)30/1 ! '
                          'nvvidconv ! '
                          'video/x-raw, width=(int){}, height=(int){}, '
                          'format=(string)BGRx ! '
                          'videoconvert ! appsink').format(1920, 1200)
        self.cap_left = cv2.VideoCapture(gst_str_video0, cv2.CAP_GSTREAMER)

        gst_str_video1 = ('nvarguscamerasrc  sensor-id=1 ! '
                          'video/x-raw(memory:NVMM), '
                          'width=(int)1920, height=(int)1200, '
                          'format=(string)NV12, framerate=(fraction)30/1 ! '
                          'nvvidconv ! '
                          'video/x-raw, width=(int){}, height=(int){}, '
                          'format=(string)BGRx ! '
                          'videoconvert ! appsink').format(1920, 1200)

        self.cap_right = cv2.VideoCapture(gst_str_video1, cv2.CAP_GSTREAMER)

        if self.cap_left:
            print('cap_left.isOpened()', self.cap_left.isOpened())

        if self.cap_right:
            print('cap_right.isOpened()', self.cap_right.isOpened())
        '''
        self.camera = ArgusCamera(0, previewWidth=1920, previewheight=1200, previewPosX=100, previewPosY=100, \
                                captureWidth=1920, captureHeight=1200, rotation=180)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.Thread_Left_Camera)
        self._timer.start(5)
        self._timer_1 = QtCore.QTimer(self)
        self._timer_1.timeout.connect(self.Thread_Right_Camera)
        self._timer_1.start(5)


    def transfer_16_bit_to_float(self,transfer_list):
        return struct.unpack('!f', bytes(transfer_list))[0]

    def Reverse(self,lst):
        new_lst = lst[::-1]
        return new_lst

    def compare_eeprom_txt_data(self,eeprom_data,txt_data):
        if round(eeprom_data,2)!=round(float(txt_data),2):
            QMessageBox.information(self, 'error', '{0} not equal to {1}'.format(eeprom_data,txt_data))
            return False
        else:
            return True

    def vertify_calibrate_process(self):
        print("========= vertify calibrate processing=========")
        self.sn_number = self.lineEdit.text()
        print(self.sn_number)
        if self.sn_number == "":
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return
        calibrate_txt_path = os.path.join(self.sn_number, "calibrate.txt")
        if not os.path.exists(calibrate_txt_path):
            QMessageBox.information(self, 'warning', 'no calibreate path %s exist' % calibrate_txt_path)
            return

        lines = []
        with open(calibrate_txt_path, "r") as f:
            for line in f.readlines():
                lines.append(line.strip().strip('\n'))

        calibrate_data_item = ["mtxR", "distR", "mtxL", "distL", "Rotate", "Translation"]
        calibrate_data_pos = []
        for item in lines:
            for calibrate_item in calibrate_data_item:
                if calibrate_item in item:
                    calibrate_data_pos.append(lines.index(item))

        mtxR_calibrate_data = lines[calibrate_data_pos[0] + 1:calibrate_data_pos[1] - 1]
        distR_calibrate_data = lines[calibrate_data_pos[1] + 1:calibrate_data_pos[2] - 1]
        mtxL_calibrate_data = lines[calibrate_data_pos[2] + 1:calibrate_data_pos[3] - 1]
        distL_calibrate_data = lines[calibrate_data_pos[3] + 1:calibrate_data_pos[4] - 1]
        Rotate_calibrate_data = lines[calibrate_data_pos[4] + 1:calibrate_data_pos[5]]
        Translation_calibrate_data = lines[calibrate_data_pos[5] + 1:calibrate_data_pos[5] + 4]

        mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[0]).replace("[[", "").replace("]", "")

        mtxR_fx = mtxR_data_list.split(",")[0]
        mtxR_cx = mtxR_data_list.split(",")[2]
        mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[1]).replace("[,", "").replace("]", "")
        mtxR_fy = mtxR_data_list.split(",")[1]
        mtxR_cy = mtxR_data_list.split(",")[2]

        mtxR_k1 = distR_calibrate_data[0].split()[0].replace("[", "")
        mtxR_k2 = distR_calibrate_data[0].split()[1]
        mtxR_p1 = distR_calibrate_data[0].split()[2]
        mtxR_p2 = distR_calibrate_data[0].split()[3]
        mtxR_k3 = distR_calibrate_data[0].split()[4]
        mtxR_k4 = distR_calibrate_data[0].split()[5]
        mtxR_k5 = distR_calibrate_data[0].split()[6]
        mtxR_k6 = distR_calibrate_data[0].split()[7]

        mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[0]).replace("[[", "").replace("]", "")
        mtxL_fx = mtxL_data_list.split(",")[0]
        mtxL_cx = mtxL_data_list.split(",")[2]
        mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[1]).replace("[,", "").replace("]", "")
        mtxL_fy = mtxL_data_list.split(",")[1]
        mtxL_cy = mtxL_data_list.split(",")[2]

        mtxL_k1 = distL_calibrate_data[0].split()[0].replace("[", "")
        mtxL_k2 = distL_calibrate_data[0].split()[1]
        mtxL_p1 = distL_calibrate_data[0].split()[2]
        mtxL_p2 = distL_calibrate_data[0].split()[3]
        mtxL_k3 = distL_calibrate_data[0].split()[4]
        mtxL_k4 = distL_calibrate_data[0].split()[5]
        mtxL_k5 = distL_calibrate_data[0].split()[6]
        mtxL_k6 = distL_calibrate_data[0].split()[7]

        Rx = self.get_no_space_string(Rotate_calibrate_data[0]).replace("[", "").split(",")[0]
        Ry = self.get_no_space_string(Rotate_calibrate_data[1]).replace("[", "").split(",")[0]
        Rz = self.get_no_space_string(Rotate_calibrate_data[2]).replace("[", "").split(",")[0]

        Tx = self.get_no_space_string(Translation_calibrate_data[0]).replace("[", "").replace("]", "").rstrip(",")
        Ty = self.get_no_space_string(Translation_calibrate_data[1]).replace("[", "").replace("]", "").rstrip(",")
        Tz = self.get_no_space_string(Translation_calibrate_data[2]).replace("[", "").replace("]", "").rstrip(",")

        sixteen_bit_data_list=self.get_16_bit_list()
        if len(sixteen_bit_data_list)==0:
            return
        mtxL_eeprom_fx=self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[16:20]))
        mtxL_eeprom_fy = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[20:24]))
        mtxL_eeprom_cx = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[28:32]))
        mtxL_eeprom_cy = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[32:36]))

        mtxL_eeprom_k1 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[44:48]))
        mtxL_eeprom_k2 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[48:52]))
        mtxL_eeprom_k3 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[52:56]))
        mtxL_eeprom_k4 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[56:60]))
        mtxL_eeprom_k5 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[60:64]))
        mtxL_eeprom_k6 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[64:68]))

        mtxL_eeprom_p1 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[72:76]))
        mtxL_eeprom_p2 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[76:80]))

        mtxR_eeprom_fx = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[88:92]))
        mtxR_eeprom_fy = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[92:96]))
        mtxR_eeprom_cx = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[100:104]))
        mtxR_eeprom_cy = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[104:108]))

        mtxR_eeprom_k1 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[116:120]))
        mtxR_eeprom_k2 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[120:124]))
        mtxR_eeprom_k3 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[124:128]))
        mtxR_eeprom_k4 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[128:132]))
        mtxR_eeprom_k5 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[132:136]))
        mtxR_eeprom_k6 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[136:140]))

        mtxR_eeprom_p1 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[144:148]))
        mtxR_eeprom_p2 = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[148:152]))

        Rx_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[152:156]))
        Ry_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[156:160]))
        Rz_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[160:164]))

        Tx_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[164:168]))
        Ty_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[168:172]))
        Tz_eeprom = self.transfer_16_bit_to_float(self.Reverse(sixteen_bit_data_list[172:176]))

        eeprom_data_list=[mtxL_eeprom_fx,mtxL_eeprom_fy,mtxL_eeprom_cx,mtxL_eeprom_cy,mtxL_eeprom_k1,mtxL_eeprom_k2,
              mtxL_eeprom_k3,mtxL_eeprom_k4,mtxL_eeprom_k5,mtxL_eeprom_k6,mtxL_eeprom_p1,mtxL_eeprom_p2,
              mtxR_eeprom_fx,mtxR_eeprom_fy,mtxR_eeprom_cx,mtxR_eeprom_cy,mtxR_eeprom_k1,mtxR_eeprom_k2,
              mtxR_eeprom_k3,mtxR_eeprom_k4,mtxR_eeprom_k5,mtxR_eeprom_k6,mtxR_eeprom_p1,mtxR_eeprom_p2,
              Rx_eeprom,Ry_eeprom,Rz_eeprom,Tx_eeprom,Ty_eeprom,Tz_eeprom]
        txt_data_list=[mtxL_fx,mtxL_fy,mtxL_cx,mtxL_cy,mtxL_k1,mtxL_k2,mtxL_k3,mtxL_k4,mtxL_k5,mtxL_k6,mtxL_p1,mtxL_p2,
            mtxR_fx,mtxR_fy,mtxR_cx,mtxR_cy,mtxR_k1,mtxR_k2,mtxR_k3,mtxR_k4,mtxR_k5,mtxR_k6,mtxR_p1,mtxR_p2,
            Rx,Ry,Rz,Tx,Ty,Tz]

        for i in range(len(eeprom_data_list)):
            if not self.compare_eeprom_txt_data(eeprom_data_list[i],txt_data_list[i]):
                return
        QMessageBox.information(self, 'info', 'compare eeprom data and txt data success')


    def get_16_bit_list(self):
        read_from_register=[]
        for i in range(256):
            count_str = "%02x" % (i)
            if self.device_name == "max9296":
                cmd = "i2ctransfer -f -y 2 w1@0x54 0x%s r1" % count_str
            else:
                cmd = "i2ctransfer -f -y 30 w1@0x54 0x%s r1" % count_str
            try:
                text = self.ExecCmd(cmd)
                read_from_register.append(int(text.rstrip("\n"),16))
            except Exception as err:
                QMessageBox.information(self, 'err', 'read eeprom data err:[%s]'%err)

        return read_from_register

    def imu_data_write_process(self):
        if self.device_name=="max9296":
            programme_cmd = os.path.join(os.getcwd(), "imu_write_to_max9296_eeprom")
        else:
            programme_cmd = os.path.join(os.getcwd(), "imu_write_to_max96712_eeprom")
        rr=subprocess.call(programme_cmd,shell=True)

    def parser_config_file(self,session, key):
        config = configparser.ConfigParser()
        config.read("device_calibrate.txt", encoding="utf-8")
        return config.get(session, key)

    def read_result(self, nextline):
        print(nextline)

    def get_no_space_string(self,str):
        return ",".join(str.split())

    def ExecCmd(self,cmd):
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    def closeEvent(self,event):
        print("close windowssssssssssssssssssssssssss")
        self._timer.stop()
        self._timer_1.stop()
        exit(0)
        #self.camera.close()

    def check_eeprom_write_process(self):
        eeprom_bin_file = os.path.join(self.sn_number, "calibrate_eeprom.bin")
        if not os.path.join(eeprom_bin_file):
            QMessageBox.information(self, 'informstion', 'write eeprom fail')
        else:
            read_from_bin_file = []
            file = open(eeprom_bin_file, 'rb')

            count = 0
            while 1:
                c = file.read(1)
                read_bytes = "0x" + str(binascii.b2a_hex(c))[2:-1]
                # print(read_bytes)
                read_from_bin_file.append(read_bytes)
                count += 1
                if count == 256:
                    break
            read_from_register = []
            count_compare = 0
            for i in range(256):
                count_str = "%02x" % (i)
                if self.device_name == "max9296":
                    cmd = "i2ctransfer -f -y 2 w1@0x54 0x%s r1" % count_str
                else:
                    cmd = "i2ctransfer -f -y 30 w1@0x54 0x%s r1" % count_str
                text = self.ExecCmd(cmd)
                read_from_register.append(text.rstrip("\n"))
                count_compare += 1
                if read_from_register[i] != read_from_bin_file[i]:
                    QMessageBox.information(self, 'information', 'write eeprom fail')
                    return False
            if count_compare == 256:
                QMessageBox.information(self, 'information', 'write eeprom success')
                return True

    def update_eeprom_data_process(self):
        print("start update eeprom data")
        self.sn_number = self.lineEdit.text()
        eeprom_bin_file = os.path.join(self.sn_number, "calibrate_eeprom.bin")
        if not os.path.join(eeprom_bin_file):
            print("no calibrate_eeprom.bin found,please check it")
            return
        else:
            file_size=os.path.getsize(eeprom_bin_file)
            print(file_size)
        file = open(eeprom_bin_file, 'rb')
        for i in range(file_size):
            c = file.read(1)
            read_bytes = str(binascii.b2a_hex(c))[2:-1]
            hex_read_byte=int(read_bytes,16)
            if self.device_name == "max9296":
                cmd = "i2ctransfer -f -y 2 w2@0x54 %d %d" % (i,hex_read_byte)
                #print(cmd)
                ret=subprocess.call(cmd,shell=True)
                if ret!=0:
                    QMessageBox.information(self, 'error', 'write eeprom data error')
                    return
            else:
                cmd = "i2ctransfer -f -y 30 w2@0x54 %d %d" % (i,hex_read_byte)
                ret = subprocess.call(cmd, shell=True)
                if ret != 0:
                    QMessageBox.information(self, 'error', 'write eeprom data error')
                    return
        self.check_eeprom_write_process()

    def download_eeprom_data_process(self):
        print("start write eeprom data")
        self.sn_number = self.lineEdit.text()
        print(self.sn_number)
        if self.sn_number == "":
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return
        calibrate_txt_path=os.path.join(self.sn_number,"calibrate.txt")
        if not os.path.exists(calibrate_txt_path):
            QMessageBox.information(self, 'warning', 'no calibreate path %s exist'%calibrate_txt_path)
            return

        lines = []
        with open(calibrate_txt_path, "r") as f:
            for line in f.readlines():
                lines.append(line.strip().strip('\n'))

        calibrate_data_item = ["mtxR", "distR", "mtxL", "distL", "Rotate", "Translation"]
        calibrate_data_pos = []
        for item in lines:
            for calibrate_item in calibrate_data_item:
                if calibrate_item in item:
                    calibrate_data_pos.append(lines.index(item))
        print(calibrate_data_pos)
        mtxR_calibrate_data = lines[calibrate_data_pos[0] + 1:calibrate_data_pos[1] - 1]
        distR_calibrate_data = lines[calibrate_data_pos[1] + 1:calibrate_data_pos[2] - 1]
        mtxL_calibrate_data = lines[calibrate_data_pos[2] + 1:calibrate_data_pos[3] - 1]
        distL_calibrate_data = lines[calibrate_data_pos[3] + 1:calibrate_data_pos[4] - 1]
        Rotate_calibrate_data = lines[calibrate_data_pos[4] + 1:calibrate_data_pos[5]]
        Translation_calibrate_data = lines[calibrate_data_pos[5] + 1:calibrate_data_pos[5] + 4]

        mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[0]).replace("[[", "").replace("]", "")


        mtxR_fx = mtxR_data_list.split(",")[0]
        mtxR_cx = mtxR_data_list.split(",")[2]
        mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[1]).replace("[,", "").replace("]", "")
        mtxR_fy = mtxR_data_list.split(",")[1]
        mtxR_cy = mtxR_data_list.split(",")[2]

        mtxR_k1 = distR_calibrate_data[0].split()[0].replace("[", "")
        mtxR_k2 = distR_calibrate_data[0].split()[1]
        mtxR_p1 = distR_calibrate_data[0].split()[2]
        mtxR_p2 = distR_calibrate_data[0].split()[3]
        mtxR_k3 = distR_calibrate_data[0].split()[4]
        mtxR_k4 = distR_calibrate_data[0].split()[5]
        mtxR_k5 = distR_calibrate_data[0].split()[6]
        mtxR_k6 = distR_calibrate_data[0].split()[7]

        mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[0]).replace("[[", "").replace("]", "")
        mtxL_fx = mtxL_data_list.split(",")[0]
        mtxL_cx = mtxL_data_list.split(",")[2]
        mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[1]).replace("[,", "").replace("]", "")
        mtxL_fy = mtxL_data_list.split(",")[1]
        mtxL_cy = mtxL_data_list.split(",")[2]

        mtxL_k1 = distL_calibrate_data[0].split()[0].replace("[", "")
        mtxL_k2 = distL_calibrate_data[0].split()[1]
        mtxL_p1 = distL_calibrate_data[0].split()[2]
        mtxL_p2 = distL_calibrate_data[0].split()[3]
        mtxL_k3 = distL_calibrate_data[0].split()[4]
        mtxL_k4 = distL_calibrate_data[0].split()[5]
        mtxL_k5 = distL_calibrate_data[0].split()[6]
        mtxL_k6 = distL_calibrate_data[0].split()[7]

        Rx = self.get_no_space_string(Rotate_calibrate_data[0]).replace("[", "").split(",")[0]
        Ry = self.get_no_space_string(Rotate_calibrate_data[1]).replace("[", "").split(",")[0]
        Rz = self.get_no_space_string(Rotate_calibrate_data[2]).replace("[", "").split(",")[0]

        Tx = self.get_no_space_string(Translation_calibrate_data[0]).replace("[", "").replace("]", "").rstrip(",")
        Ty = self.get_no_space_string(Translation_calibrate_data[1]).replace("[", "").replace("]", "").rstrip(",")
        Tz = self.get_no_space_string(Translation_calibrate_data[2]).replace("[", "").replace("]", "").rstrip(",")

        bin_file=os.path.join(self.sn_number,"calibrate_eeprom.bin")
        print("device_name={0}".format(self.device_name))
        if self.device_name=="max9296":
            programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max9296")
        else:
            programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max96712")

        cmd = programme_cmd + " %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" \
            %(mtxR_fx,mtxR_fy,mtxR_cx,mtxR_cy,mtxR_k1,mtxR_k2,mtxR_p1,mtxR_p2,mtxR_k3,mtxR_k4,mtxR_k5,mtxR_k6,mtxL_fx,mtxL_fy,
            mtxL_cx,mtxL_cy,mtxL_k1,mtxL_k2,mtxL_p1,mtxL_p2,mtxL_k3,mtxL_k4,mtxL_k5,mtxL_k6,Rx,Ry,Rz,Tx,Ty,Tz,bin_file)

        print(cmd)

        self.process = QtCore.QProcess()

        self.process.start(cmd)
        self.process.readyReadStandardOutput.connect(
            lambda: self.read_result(str(self.process.readAllStandardOutput().data().decode('utf-8'))))
        #self.process.waitForStarted()
        self.process.waitForFinished()

        #print("111111111111111111111111111")
        self.check_eeprom_write_process()
        self.process.kill()


    def Thread_Left_Camera(self):
        global frame_left
        ret_left, frame_left = self.camera.read()
        if ret_left:
            rgbImage = cv2.cvtColor(frame_left, cv2.COLOR_BGR2RGB)
            convertToQtFormat = QtGui.QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0],
                                             QImage.Format_RGB888)
            p = convertToQtFormat.scaled(1920, 1200, Qt.KeepAspectRatio)
            Pixmap = QPixmap.fromImage(p)
            self.label.setScaledContents(True)
            self.label.setPixmap(Pixmap)
            #self.changePixmap.emit(p)

    def Thread_Right_Camera(self):
        global frame_right
        ret_right, frame_right = self.camera.read_1()
        if ret_right:
            rgbImage1 = cv2.cvtColor(frame_right, cv2.COLOR_BGR2RGB)
            convertToQtFormat1 = QtGui.QImage(rgbImage1.data, rgbImage1.shape[1], rgbImage1.shape[0],
                                              QImage.Format_RGB888)
            p1 = convertToQtFormat1.scaled(1920, 1200, Qt.KeepAspectRatio)
            Pixmap = QPixmap.fromImage(p1)
            self.label_2.setScaledContents(True)
            self.label_2.setPixmap(Pixmap)
            #self.changePixmap.emit(p1)

    def calibration(self):
        """
        start one thread for calibration
        :return: none
        """
        thread_calibration = threading.Thread(target=self.calibration_opencv)
        thread_calibration.start()

    def calibration_opencv(self):
        self.sn_number = self.lineEdit.text()
        print(self.sn_number)
        if self.sn_number!="":
            save_result = self.sn_number
        else:
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return

        global FLAG
        global dict_left_calibrate_pic_error
        global dict_right_calibrate_pic_error

        dict_left_calibrate_pic_error.clear()
        dict_right_calibrate_pic_error.clear()
        print("=========== start calibrte  =========")

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
        objp = np.zeros((10 * 16, 3),
                        np.float32)  # I used a 10×16 checkerboard, and you could modify the relevant parameters according to your checkerboard
        objp[:, :2] = np.mgrid[0:16, 0:10].T.reshape(-1, 2)
        objpoints = []  # 3d points in real world space
        imgpointsR = []  # 2d points in image plane
        imgpointsL = []

        if (not os.path.exists(save_result)):
            os.makedirs(save_result)

        img_right_path = save_result+'/right/*.jpg'
        img_left_path = save_result+'/left/*.jpg'
        images_right = glob.glob(img_right_path)
        images_right.sort()
        img_show_righ_path = images_right[0]
        images_left = glob.glob(img_left_path)
        images_left.sort()
        img_show_left_path = images_left[0]

        if len(images_left)!=len(images_right):
            QMessageBox.information(self,"Message","length of left is {0} is not equal to length of right {1}".format(len(images_left),len(images_right)))
            return

        find_right_file=[]
        find_left_file=[]

        for fname_left, fname_right in zip(images_left, images_right):
            ChessImaR = cv2.imread(fname_right)  # Right view
            ChessImaR_gray = cv2.cvtColor(ChessImaR, cv2.COLOR_BGR2GRAY)
            ChessImaL = cv2.imread(fname_left)  # The left view
            ChessImaL_gray = cv2.cvtColor(ChessImaL, cv2.COLOR_BGR2GRAY)
            flag_left = 0
            flag_left |= cv2.CALIB_CB_ADAPTIVE_THRESH
            flag_left |= cv2.CALIB_CB_FILTER_QUADS
            flag_left |= cv2.CALIB_CB_FAST_CHECK
            flag_right = 0
            flag_right |= cv2.CALIB_CB_ADAPTIVE_THRESH
            # After many tests, it was found that the following parameters should not be set for the images with large deformation in the close middle,
            # otherwise the checkerboard could not be reached easily
            # flag_right |= cv2.CALIB_CB_NORMALIZE_IMAGE
            retR, cornersR = cv2.findChessboardCorners(ChessImaR_gray, (16, 10), None,
                                                       flags=flag_right)  # Extract the corners of each image on the right

            retL, cornersL = cv2.findChessboardCorners(ChessImaL_gray, (16, 10), None,
                                                       flags=flag_left)  # Extract the corners of each image on the left
            if not retL or not retR:
                dict_left_calibrate_pic_error[fname_left]="no find"
                dict_right_calibrate_pic_error[fname_right] = "no find"

            if (True == retR) & (True == retL):
                objpoints.append(objp)
                cv2.cornerSubPix(ChessImaR_gray, cornersR, (11, 11), (-1, -1),
                                 criteria)  # Subpixel precision, the rough extraction of the corner of the precision
                cv2.cornerSubPix(ChessImaL_gray, cornersL, (11, 11), (-1, -1),
                                 criteria)  # Subpixel precision, the rough extraction of the corner of the precision
                find_left_file.append(fname_left)
                find_right_file.append(fname_right)

                imgpointsR.append(cornersR)
                imgpointsL.append(cornersL)
        #  Calibrate the right camera separately
        flag_right_calibaration = 0
        # If the following parameters are used, 8 deformation parameters will be used, K4,K5, and K6 will be activated
        flag_right_calibaration |= cv2.CALIB_RATIONAL_MODEL
        retR, mtxR, distR, rvecsR, tvecsR, stdDeviationsIntrinsics_R, stdDeviationsExtrinsics_R, perViewErrors_R = cv2.calibrateCameraExtended(
            objpoints, imgpointsR, ChessImaR_gray.shape[::-1], None, None, flags=flag_right_calibaration, criteria=criteria)

        #   Subsequent to get new camera matrix initUndistortRectifyMap to generate mapping relationship with remap
        hR, wR = ChessImaR.shape[:2]
        OmtxR, roiR = cv2.getOptimalNewCameraMatrix(mtxR, distR, (wR, hR), 1, (wR, hR))
        flag_left_calibration = 0
        # If the following parameters are used, 8 deformation parameters will be used, K4,K5, and K6 will be activated
        flag_left_calibration |= cv2.CALIB_RATIONAL_MODEL
        # Calibrate the left camera separately
        retL, mtxL, distL, rvecsL, tvecsL, stdDeviationsIntrinsics_L, stdDeviationsExtrinsics_L, perViewErrors_L = cv2.calibrateCameraExtended(
            objpoints, imgpointsL, ChessImaL_gray.shape[::-1], None, None, flags=flag_left_calibration, criteria=criteria)

        mean_error_right = 0
        print("len(objpoints)=", len(objpoints))
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsR[i], tvecsR[i], mtxR, distR)
            error = cv2.norm(imgpointsR[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            print("right pic:{0},error:{1}".format(find_right_file[i],error))
            dict_right_calibrate_pic_error[find_right_file[i]]=str(error)
            mean_error_right += error
        mean_reproject_error_right = mean_error_right / len(objpoints)
        print("right reproject error : ", mean_reproject_error_right)

        mean_error_left = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsL[i], tvecsL[i], mtxL, distL)
            error = cv2.norm(imgpointsL[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            print("left pic:{0},error:{1}".format(find_left_file[i], error))
            dict_left_calibrate_pic_error[find_left_file[i]]=str(error)
            mean_error_left += error
        mean_reproject_error_left = mean_error_left / len(objpoints)
        print("left reproject error  : ", mean_reproject_error_left)

        print('mean reproject error', (mean_reproject_error_left + mean_reproject_error_right) / 2)


        #  Subsequent to get new camera matrix initUndistortRectifyMap to generate mapping relationship with remap
        hL, wL = ChessImaL.shape[:2]
        OmtxL, roiL = cv2.getOptimalNewCameraMatrix(mtxL, distL, (wL, hL), 1, (wL, hL))
        # Calibration of binocular cameras
        flags_two = 0
        flags_two |= cv2.CALIB_USE_INTRINSIC_GUESS
        flags_two |= cv2.CALIB_RATIONAL_MODEL
        retS, MLS, dLS, MRS, dRS, R, T, E, F, perViewErrors = cv2.stereoCalibrateExtended(objpoints, imgpointsL, imgpointsR,
                                                                                          mtxL, distL, mtxR, distR,
                                                                                          ChessImaR_gray.shape[::-1], None,
                                                                                          None, criteria=criteria,
                                                                                          flags=flags_two)
        print('retS', retS)
        print('distL', distL)
        print('dLS', dLS)
        print('distR', distR)
        print('dRS', dRS)
        #print('perViewErrors', perViewErrors)
        # Using stereoequal equal (), compute the stereoadjusted mapping matrix
        rectify_scale = 1  # If set to 0, the image is cropped, and if set to 1, all original image pixels are retained
        RL, RR, PL, PR, Q, roiL, roiR = cv2.stereoRectify(MLS, dLS, MRS, dRS,
                                                          ChessImaR_gray.shape[::-1], R, T,
                                                          rectify_scale, (0, 0))


        x_left, y_left, w_left, h_left = roiL
        x_right, y_right, w_right, h_right = roiR
        # InitUndistortRectifyMap function is used to calculate distortion correction and calibration stereo mapping transformation, realize the polar alignment.
        Left_Stereo_Map = cv2.initUndistortRectifyMap(MLS, dLS, RL, PL,
                                                      ChessImaR_gray.shape[::-1], cv2.CV_16SC2)
        Right_Stereo_Map = cv2.initUndistortRectifyMap(MRS, dRS, RR, PR,
                                                       ChessImaR_gray.shape[::-1], cv2.CV_16SC2)

        # Stereo correction effect display
        frameR = cv2.imread(img_show_righ_path)
        frameL = cv2.imread(img_show_left_path)
        #frameR = cv2.imread("char_left.jpg")
        #frameL = cv2.imread("char_right.jpg")
        Left_rectified = cv2.remap(frameL, Left_Stereo_Map[0], Left_Stereo_Map[1], cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT,
                                   0)  # The remap function is used to complete the mapping
        # Left_rectified = Left_rectified[y_left:y_left+h_left,x_left:x_left+w_left]
        cv2.imwrite(save_result + '/left.jpg', Left_rectified)
        im_L = Image.fromarray(Left_rectified)  # numpy to image
        Right_rectified = cv2.remap(frameR, Right_Stereo_Map[0], Right_Stereo_Map[1], cv2.INTER_LANCZOS4,
                                    cv2.BORDER_CONSTANT, 0)
        # Right_rectified = Right_rectified[y_right:y_right + h_right, x_right:x_right + w_right]
        cv2.imwrite(save_result + '/right.jpg', Right_rectified)
        im_R = Image.fromarray(Right_rectified)  # numpy 转 image 类
        # Create an area where you can put two pictures side by side and paste them in one after the other
        width = im_L.size[0] * 2
        height = im_L.size[1]
        img_compare = Image.new('RGBA', (width, height))
        img_compare.paste(im_L, box=(0, 0))
        img_compare.paste(im_R, box=(1920, 0))
        # Line evenly an image that has been pole-aligned
        save_img = np.array(img_compare)
        for i in range(1, 20):
            h_len = int(1200 / 20)
            cv2.line(save_img, (0, i * h_len), (3840, i * h_len), (0, 0, 255), 2)
        cv2.imwrite(save_result + '/two.jpg', save_img)
        #save_data = './result'
        #if not os.path.exists(save_data):
        #    os.mkdir(save_data)
        R=cv2.Rodrigues(R)[0]
        print(str(R))
        with open(save_result + "/calibrate.txt", 'w') as f:
            f.write('retR :: ' + str(retR) + '\n')
            f.write('mtxR :: ' + '\n')
            for i in range(mtxR.shape[0]):
                if i==0:
                    f.write("[[")
                else:
                    f.write(" [")
                for j in range(mtxR.shape[1]):
                    f.write(str(mtxR[i][j]) + " ")
                if i==2:
                    f.write("]]")
                else:
                    f.write("]")
                f.write('\n')
            #f.write(str(mtxR))
            #f.write('\n')
            f.write('distR :: ' + '\n')
            # f.write(str(distR[0:6][0]))
            for i in range(distR.shape[0]):
                f.write("[")
                for j in range(distR.shape[1]):
                    f.write(str(distR[i][j]) + " ")
                f.write("]")
            f.write('\n')
            f.write('retL :: ' + str(retL) + '\n')
            f.write('mtxL :: ' + '\n')
            #f.write(str(mtxL))
            for i in range(mtxL.shape[0]):
                if i==0:
                    f.write("[[")
                else:
                    f.write(" [")
                for j in range(mtxL.shape[1]):
                    f.write(str(mtxL[i][j]) + " ")
                if i==2:
                    f.write("]]")
                else:
                    f.write("]")
                f.write('\n')
            f.write('distL :: ' + '\n')
            for i in range(distL.shape[0]):
                f.write("[")
                for j in range(distL.shape[1]):
                    f.write(str(distL[i][j]) + " ")
                f.write("]")
            f.write('\n')

            f.write('retS   ' + str(retS) + '\n')
            f.write("Rotate ::" + '\n')
            for i in range(R.shape[0]):
                f.write("[")
                for j in range(R.shape[1]):
                    f.write(str(R[i][j]) + " ")
                f.write("]")
                f.write('\n')

            #f.write(str(R))

            f.write("Translation ::" + '\n')
            for i in range(T.shape[0]):
                f.write("[")
                for j in range(T.shape[1]):
                    f.write(str(T[i][j]) + " ")
                f.write("]")
                f.write('\n')

            f.write("E ::" + '\n')
            f.write(str(E))
            f.write('\n')

            f.write("F ::" + '\n')
            f.write(str(F))
            f.write('\n')

            f.write("Q::" + '\n')
            f.write(str(Q))
            f.write('\n')

            f.write("left reproject error  :  " + str(mean_reproject_error_left) + '\n')
            f.write("right reproject error  :  " + str(mean_reproject_error_right) + '\n')
            f.write("mean reproject error  :  " + str((mean_reproject_error_left + mean_reproject_error_right) / 2) + '\n')
        print("============ calibrate ending ======================")
        FLAG = True
        '''
        calibrate_end_image = cv2.imread(os.path.join(save_data,"two.jpg"))
        height, width = calibrate_end_image.shape[:2]
        shrink_img = cv2.resize(calibrate_end_image, (int(width / 4), int(height / 2)), interpolation=cv2.INTER_AREA)
        cv2.imshow("calibrate image", shrink_img)
        cv2.waitKey(1)
        '''

    def setImage_left(self, image):
        """
        show image on label_left_camera
        :return: none
        """
        self.label_left_camera.setPixmap(QPixmap.fromImage(image))

    def setImage_right(self, image):
        """
        show image on label_right_camera
        :return: none
        """
        self.label_right_camera.setPixmap(QPixmap.fromImage(image))

    def capture_image(self):
        self.sn_number = self.lineEdit.text()
        print(self.sn_number)
        if self.sn_number!=self.old_sn_number:
            self.capture_num=0
            self.old_sn_number=self.sn_number
            self.ch.iconlist.clear()

        if self.sn_number != "":
            save_result = self.sn_number
        else:
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return

        if (not os.path.exists(save_result)):
            os.makedirs(save_result)

        if os.path.exists(os.path.join(save_result,"left")) is False:
            os.makedirs(os.path.join(save_result,"left"))
        if os.path.exists(os.path.join(save_result,"right")) is False:
            os.makedirs(os.path.join(save_result,"right"))
        img_left_path = os.path.join(save_result,"left")+"/%02d"%self.capture_num + '.jpg'
        img_right_path =os.path.join(save_result,"right")+"/%02d"%self.capture_num + '.jpg'

        #if self.cap_left.isOpened() == True:
        global CAPTURE_FLAG
        CAPTURE_FLAG = True
        global capture_path
        #global frame_left
        capture_path = img_left_path
        #frame_left=cv2.resize(frame_left,(1920,1200),interpolation=cv2.INTER_AREA)
        cv2.imwrite(img_left_path, frame_left)
        self.ch.additems()

        #if self.cap_right.isOpened() == True:
        global RIGHT_CAPTURE_FLAG
        RIGHT_CAPTURE_FLAG = True
        global right_capture_path
        #global frame_right
        right_capture_path = img_right_path
        #frame_right = cv2.resize(frame_right, (1920, 1200), interpolation=cv2.INTER_AREA)
        cv2.imwrite(img_right_path, frame_right)
        self.ch.additems()
        self.capture_num+=1


class IconListWidget(QWidget):
    def __init__(self, parent=None):
        super(IconListWidget, self).__init__(parent)
        #self.resize(800, 900)
        self.setFixedSize(800, 900)
        self.setWindowTitle("calibrate result show")
        self.setupUi()

    def setupUi(self):
        self.iconlist = QListWidget()
        self.iconlist.setViewMode(QListView.IconMode)
        self.iconlist.setSpacing(10)
        self.iconlist.setSizeAdjustPolicy(True)
        self.iconlist.setIconSize(QSize(100, 100))
        self.iconlist.setMovement(False)
        self.iconlist.setResizeMode(QListView.Adjust)
        #self.iconlist.setFixedSize(1920,400)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.iconlist)
        self.setLayout(hlayout)

        self.iconlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.iconlist.customContextMenuRequested.connect(self.contextMenuEvent)


        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.show_calibrate_items)
        self._timer.start(5)

        self._timer_1 = QtCore.QTimer(self)
        self._timer_1.timeout.connect(self.additems)
        self._timer_1.start(5)


    def contextMenuEvent(self, point):
        pmenu = QMenu(self)
        try:
            pDelGroupAct = QAction("delete", pmenu)
            pmenu.addAction(pDelGroupAct)
            pDelGroupAct.triggered.connect(self.DeleteItem)
        except Exception as err:
            print(err)

        pmenu.exec_(self.iconlist.mapToGlobal(point))

    def DeleteItem(self):
        current_row_position=self.iconlist.currentRow()
        delete_file_name=self.iconlist.item(current_row_position).text().split(":")[0]
        #specific_file_name=delete_file_name.split("/")[-1].strip()
        #print("remove left pic name:",os.path.join("left",specific_file_name))
        #print("remove right pic name:", os.path.join("right", specific_file_name))
        if os.path.exists(delete_file_name):
            os.remove(delete_file_name)
        

        QMessageBox.information(self,"Message","delete picture %s"%delete_file_name)
        self.iconlist.takeItem(self.iconlist.currentRow())

    def additems(self):
        # 读取缩略图
        global CAPTURE_FLAG
        global capture_path
        global RIGHT_CAPTURE_FLAG
        global right_capture_path
        if CAPTURE_FLAG:
            CAPTURE_FLAG = False
            text_str=capture_path+":0.0000"
            item = QListWidgetItem(QtGui.QIcon(capture_path), text_str)
            self.iconlist.addItem(item)
            self.iconlist.setIconSize(QSize(350, 350))

        if RIGHT_CAPTURE_FLAG:
            RIGHT_CAPTURE_FLAG=False
            text_str = right_capture_path + ":0.0000"
            item = QListWidgetItem(QtGui.QIcon(right_capture_path), text_str)
            self.iconlist.addItem(item)
            self.iconlist.setIconSize(QSize(350, 350))

    def show_calibrate_items(self):
        global FLAG

        if FLAG:
            self.iconlist.clear()
            for left_key,right_key in zip(dict_left_calibrate_pic_error,dict_right_calibrate_pic_error):
                try:
                    item = QListWidgetItem(QtGui.QIcon(left_key), left_key+":"+dict_left_calibrate_pic_error[left_key])
                    # item.setTextAlignment(QtCore.Qt.AlignRight)
                    # item.setSizeHint(QSize(400,400))
                    self.iconlist.addItem(item)
                    self.iconlist.setIconSize(QSize(350, 350))
                except Exception as err:
                    print("err:",err)

                item = QListWidgetItem(QtGui.QIcon(right_key), right_key + ":" + dict_right_calibrate_pic_error[right_key])
                # item.setTextAlignment(QtCore.Qt.AlignRight)
                # item.setSizeHint(QSize(400,400))
                self.iconlist.addItem(item)
                self.iconlist.setIconSize(QSize(350, 350))
            FLAG=False


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.window_init()
    window.show()
    sys.exit(app.exec_())
