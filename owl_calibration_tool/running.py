import sys, time
from camera_tool import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import  *
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt,pyqtSlot,QRect
from PyQt5.QtGui import QPixmap, QImage,QBrush,QColor,QIcon
from utils import *
import cv2
from ctypes import *
import datetime
from PIL import ImageQt
from PIL import Image
import binascii

from argusCamera import ArgusCamera, ArgusStrOverlay, ArgusRectOverlay
import threading
try:
    import Queue as Queue
except:
    import queue as Queue
import json

import glob

dict_right_calibrate_pic_error={}
dict_left_calibrate_pic_error={}
FLAG=False
CAPTURE_FLAG=False
RIGHT_CAPTURE_FLAG=False


class IconListWidget(QWidget):
    def __init__(self, parent=None):
        super(IconListWidget, self).__init__(parent)
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
        print("remove left pic name:",delete_file_name)
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
        #print("FLAG={0}".format(FLAG))
        if FLAG:
            print("show calibrate result")
            self.iconlist.clear()
            if dict_right_calibrate_pic_error:
                for left_key, right_key in zip(dict_left_calibrate_pic_error, dict_right_calibrate_pic_error):
                    item = QListWidgetItem(QtGui.QIcon(left_key),
                                               left_key + ":" + dict_left_calibrate_pic_error[left_key])
                    self.iconlist.addItem(item)
                    self.iconlist.setIconSize(QSize(350, 350))

                    item = QListWidgetItem(QtGui.QIcon(right_key),
                                           right_key + ":" + dict_right_calibrate_pic_error[right_key])
                    self.iconlist.addItem(item)
                    self.iconlist.setIconSize(QSize(350, 350))

            else:
                for left_key in dict_left_calibrate_pic_error:
                    try:
                        item = QListWidgetItem(QtGui.QIcon(left_key), left_key+":"+dict_left_calibrate_pic_error[left_key])
                        self.iconlist.addItem(item)
                        self.iconlist.setIconSize(QSize(350, 350))
                    except Exception as err:
                        print("err:",err)

            FLAG=False


class Video_Worker(QtCore.QThread):
    # Signals
    #log_message = qtc.pyqtSignal(str)
    img_signal = QtCore.pyqtSignal(QPixmap)
    finished_taking_photos = QtCore.pyqtSignal(bool)

    def __init__(
            self,
            cam_cfg,
            resized_width: int, resized_height: int,
            VideoLabel,
            current_fps,
            parent
    ) -> None:
        """
        Initialize variables used in this QThread.

        Args:
            cam_cfg (dict): dictionary for camera parameters
            pause_pixmap (QPixmap): the pause image
            resized_width (int): width of the resized resolution
            resized_height (int): height of the resized resolution
        """
        super().__init__(parent)
        self.cam_cfg = cam_cfg
        self.camera_model = "None"
        self.camera = None
        self.VideoLabel=VideoLabel
        self.img = None
        self.demosaic = None
        self.ret = False
        self.resized_width = resized_width
        self.resized_height = resized_height
        self.current_fps=current_fps
        self.running = True
        self.taking_photos = False


    def create_camera_object(self):
        #if self.cam_cfg["camera"]["use_directshow"] != 1:
        camera = cv2.VideoCapture(self.cam_cfg["camera"]["cam_index"])
        print(camera)
        camera.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        #camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_cfg["camera"]["reso_w"])  # set image width
        #camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_cfg["camera"]["reso_h"])  # set image height
        #self.camera.set(cv2.CAP_PROP_GAIN, self.cam_cfg["camera"]["gain"])
        camera.read()
        print(camera.read())
        #if self.cam_cfg["camera"]["data_format"] == "RAW":
        #    camera.set(cv2.CAP_PROP_CONVERT_RGB, 0)  # Do not convert to RGB

        return camera

    def stop_running(self):
        """
        Once this function is called, the while loop in run() is broken.
        """
        self.running = False

    def run(self):
        print("video process start")

        camera_is_opened = False

        print("check camera down")
        try:
            self.camera = self.create_camera_object()
            camera_is_opened = self.camera.isOpened()
        except Exception as err:
            print(err)

        prev_frame_time=0

        print("camera_is_opened:{0}".format(camera_is_opened))
        while self.running:
            if not camera_is_opened:
                try:
                    self.camera.release()
                except Exception as err:
                    print("{%s},Unable to release camera."%err)
                time.sleep(0.5)

                camera_is_opened = self.camera.isOpened()
                if camera_is_opened:
                    pass
                    #cr_date = datetime.now().strftime("%m_%d_%Y %H:%M:%S").split()
                else:
                    #self.img_signal.emit(self.pause_pixmap)
                    continue

            # Capture frame-by-frame
            self.ret, frame = self.camera.read()
            #print("frame={0}".format(frame))
            if not self.ret:
                try:
                    time.sleep(0.05)
                    #self.check_camera_connection()
                except:
                    pass

                if self.camera_model != self.cam_cfg["camera"]["cam_model"]:
                    #cr_date = datetime.now().strftime("%m_%d_%Y %H:%M:%S").split()
                    camera_is_opened = False
                continue

            if self.cam_cfg["camera"]["data_format"] == "RAW":  # Raw camera only
                raw = np.frombuffer(frame, dtype=np.uint16)
                raw16 = np.left_shift(raw, (16 - self.cam_cfg['camera']["raw_bits"]))
                bayer = np.reshape(raw16, (-1, self.cam_cfg['camera']["reso_w"]))

                # Perform a Bayer reconstruction
                try:
                    if self.cam_cfg["camera"]["color"] == 0:
                        self.demosaic = cv2.cvtColor(bayer, self.cam_cfg['camera']["bayer_conversion"] + 40)
                    else:
                        self.demosaic = cv2.cvtColor(bayer, self.cam_cfg['camera']["bayer_conversion"])
                except Exception as err:
                    print(err)
                    continue
                # Resize
                self.img = self.demosaic.copy()
                self.img = cv2.resize(self.img, (int(self.resized_width), int(self.resized_height)))
                self.img = (self.img / 256).astype('uint8')

                #print("self.img={0}".format(self.img))
            elif self.cam_cfg["camera"]["data_format"] == "YUV":
                # YUV422 camera
                self.demosaic = frame
                # Color conversion
                self.demosaic = np.reshape(self.demosaic,
                                           (self.cam_cfg["camera"]["reso_h"], self.cam_cfg["camera"]["reso_w"], 2))
                try:
                    if self.cam_cfg["camera"]["color"] == 0:
                        self.demosaic = cv2.cvtColor(self.demosaic, cv2.COLOR_YUV2GRAY_YVYU)
                    else:
                        self.demosaic = cv2.cvtColor(self.demosaic, cv2.COLOR_YUV2RGB_YVYU)
                except:
                    continue
                self.img = self.demosaic.copy()
                self.img = cv2.resize(self.img, (int(self.resized_width), int(self.resized_height)))
            else:
                continue

            new_frame_time = time.time()  # Time of processing one frame
            try:
                fps = round(1 / (new_frame_time - prev_frame_time), 1)  # Calculate frames per second
            except:
                fps = 0.0
            prev_frame_time = new_frame_time
            #self.current_fps.setText("{0}".format(fps))

            Qimg = QImage(
                self.img.data,
                self.img.shape[1],
                self.img.shape[0],
                self.img.shape[1] * 3,
                QImage.Format_RGB888
            ).rgbSwapped()  # Convert array to QImage

            try:
                img_pixmap = QPixmap.fromImage(Qimg)  # Convert QImage to QPixmap

            except Exception as err:
                print("Convert QImage to QPixmap {%s}"%err)
                continue

            #print("begin show video to label")
            self.img_signal.emit(img_pixmap)


class camera_tool_setup(QMainWindow,Ui_MainWindow):
    def __init__(self,s_args):
        super(camera_tool_setup,self).__init__()
        self.setupUi(self)
        self.setWindowTitle("lepard calibrate tool V1.0.0")
        self.setWindowIcon(QIcon('leopard-logo.ico'))
        self.ch = IconListWidget()
        self.ch.show()

        self.cam_config_file_path = s_args.camera_config_file
        if not os.path.exists(self.cam_config_file_path):
            QMessageBox.information(self,"error","no config file [%s] found"%self.cam_config_file_path)
            sys.exit()

        config_json = open(self.cam_config_file_path, "r")
        self.cam_cfg = json.loads(config_json.read())
        self.resized_width=self.cam_cfg["camera"]["reso_w"]
        self.resized_height = self.cam_cfg["camera"]["reso_h"]
        self.current_device_name.setText(self.cam_cfg["camera"]["cam_model"])
        self.current_res.setText("{0}X{1}".format(self.resized_width,self.resized_height))
        self.device_name=self.cam_cfg["camera"]["device_name"]

        self.chessboard_height=self.cam_cfg["camera"]["board_size_h"]
        self.chessboard_with=self.cam_cfg["camera"]["board_size_w"]
        self.i2cAddr=self.cam_cfg["camera"]["i2c_addr"]

        self.CaptureButton.clicked.connect(self.captureImageProcess)
        self.CalibrateButton.clicked.connect(self.calibrateProcess)
        self.DownloadButton.clicked.connect(self.download_eeprom_data_process)

        self.camera = ArgusCamera(0, previewWidth=self.resized_width, previewheight=self.resized_height, previewPosX=100, previewPosY=100,captureWidth=self.resized_width, captureHeight=self.resized_height, rotation=180)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.Thread_Left_Camera)
        self._timer.start(5)
        #self._timer_1 = QtCore.QTimer(self)
        #self._timer_1.timeout.connect(self.Thread_Right_Camera)
        #self._timer_1.start(5)
        '''
        self.video_thread = Video_Worker(
            self.cam_cfg,
            self.resized_width, self.resized_height,
            self.Videolabel,
            self.current_framerate,
            parent=self
        )
        self.video_thread.img_signal.connect(self.display_to_label)
        self.video_thread.start()  # Start the video thread
        '''
        #self.camera = cv2.VideoCapture(self.cam_cfg["camera"]["cam_index"])
        #self._timer = QtCore.QTimer(self)
        #self._timer.timeout.connect(self.Thread_Left_Camera)
        #self._timer.start(5)

    def check_eeprom_write_process(self):
        eeprom_bin_file = os.path.join(self.sn_number, "result", "calibate_eeprom.bin")
        if not os.path.join(eeprom_bin_file):
            QMessageBox.information(self, 'informstion', 'write eeprom fail')
            return
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
                # i2ctransfer -f -y 30 w2@0x%02x 0x%x 0x%x
                if self.device_name == "max96712":
                    # cmd = "i2ctransfer -f -y 30 w1@0x54 0x%s r1" % count_str
                    cmd = "i2ctransfer -f -y 30 w1@%s 0x%s r1" % (self.i2cAddr,count_str)
                else:
                    cmd = "i2ctransfer -f -y 2 w1@%s 0x%s r1" % (self.i2cAddr,count_str)
                print(cmd)
                text = self.ExecCmd(cmd)
                read_from_register.append(text.rstrip("\n"))
                count_compare += 1
                if read_from_register[i] != read_from_bin_file[i]:
                    QMessageBox.information(self, 'information', 'write eeprom fail')
                    return False
            if count_compare == 256:
                QMessageBox.information(self, 'information', 'write eeprom success')
                return True


    def download_eeprom_data_process(self):
        print("start write eeprom data")
        self.sn_number = self.snlineEdit.text()
        if self.sn_number == "":
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return

        save_result = os.path.join(self.sn_number, "result")
        calibrate_txt_path = os.path.join(self.sn_number, "result", "calibrate.txt")
        if not os.path.exists(calibrate_txt_path):
            QMessageBox.information(self, 'warning', 'no calibreate path %s exist' % calibrate_txt_path)
            return

        lines = []
        with open(calibrate_txt_path, "r") as f:
            for line in f.readlines():
                lines.append(line.strip().strip('\n'))
        if self.cam_cfg['camera']['calibrate_type'] != "stereo":
            calibrate_data_item = ["mtxL", "distL"]
            calibrate_data_pos = []
            for item in lines:
                for calibrate_item in calibrate_data_item:
                    if calibrate_item in item:
                        calibrate_data_pos.append(lines.index(item))
            print(calibrate_data_pos)
            # mtxR_calibrate_data = lines[calibrate_data_pos[0] + 1:calibrate_data_pos[1] - 1]
            # distR_calibrate_data = lines[calibrate_data_pos[1] + 1:calibrate_data_pos[2] - 1]
            mtxL_calibrate_data = lines[calibrate_data_pos[0] + 1:calibrate_data_pos[1] - 1]
            distL_calibrate_data = lines[calibrate_data_pos[1] + 1:calibrate_data_pos[1] + 2]
            print(mtxL_calibrate_data)

            # Rotate_calibrate_data = lines[calibrate_data_pos[4] + 1:calibrate_data_pos[5]]
            # Translation_calibrate_data = lines[calibrate_data_pos[5] + 1:calibrate_data_pos[5] + 4]

            # mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[0]).replace("[[", "").replace("]", "")

            mtxR_fx = 0
            mtxR_cx = 0
            # mtxR_data_list = self.get_no_space_string(mtxR_calibrate_data[1]).replace("[,", "").replace("]", "")
            mtxR_fy = 0
            mtxR_cy = 0

            mtxR_k1 = 0
            mtxR_k2 = 0
            mtxR_p1 = 0
            mtxR_p2 = 0
            mtxR_k3 = 0
            mtxR_k4 = 0
            mtxR_k5 = 0
            mtxR_k6 = 0

            mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[0]).replace("[[", "").replace("]", "")

            mtxL_fx = mtxL_data_list.split(",")[0]
            mtxL_cx = mtxL_data_list.split(",")[2]
            mtxL_data_list = self.get_no_space_string(mtxL_calibrate_data[1]).replace("[,", "").replace("]", "")
            mtxL_fy = mtxL_data_list.split(",")[1]
            mtxL_cy = mtxL_data_list.split(",")[2]

            print(distL_calibrate_data)
            if self.camera_flag == "fisheye":
                mtxL_k1 = distL_calibrate_data[0].split()[0].replace("[", "")
                mtxL_k2 = distL_calibrate_data[0].split()[1]
                mtxL_p1 = 0
                mtxL_p2 = 0
                mtxL_k3 = distL_calibrate_data[0].split()[2]
                mtxL_k4 = distL_calibrate_data[0].split()[3]
                mtxL_k5 = 0
                mtxL_k6 = 0
            else:
                mtxL_k1 = distL_calibrate_data[0].split()[0].replace("[", "")
                mtxL_k2 = distL_calibrate_data[0].split()[1]
                mtxL_p1 = distL_calibrate_data[0].split()[2]
                mtxL_p2 = distL_calibrate_data[0].split()[3]
                mtxL_k3 = distL_calibrate_data[0].split()[4]
                mtxL_k4 = distL_calibrate_data[0].split()[5]
                mtxL_k5 = distL_calibrate_data[0].split()[6]
                mtxL_k6 = distL_calibrate_data[0].split()[7]

            Rx = 0
            Ry = 0
            Rz = 0

            Tx = 0
            Ty = 0
            Tz = 0

            bin_file = os.path.join(self.sn_number, "result", "calibate_eeprom.bin")
            print("device_name={0}".format(self.device_name))

            if self.device_name == "max96712":
                programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max96712")
            else:
                programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max9296")

            cmd = programme_cmd + " %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %d %d" \
                  % (mtxR_fx, mtxR_fy, mtxR_cx, mtxR_cy, mtxR_k1, mtxR_k2, mtxR_p1, mtxR_p2, mtxR_k3, mtxR_k4, mtxR_k5,
                     mtxR_k6,
                     mtxL_fx, mtxL_fy,
                     mtxL_cx, mtxL_cy, mtxL_k1, mtxL_k2, mtxL_p1, mtxL_p2, mtxL_k3, mtxL_k4, mtxL_k5, mtxL_k6, Rx, Ry,
                     Rz, Tx,
                     Ty, Tz, bin_file, self.camera_flag, self.pic_width, self.pic_height)

            print(cmd)
        else:
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

            bin_file = os.path.join(self.sn_number, "calibrate_eeprom.bin")
            print("device_name={0}".format(self.device_name))
            if self.device_name == "max9296":
                programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max9296")
            else:
                programme_cmd = os.path.join(os.getcwd(), "eeprom_flash_max96712")

            cmd = programme_cmd + " %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" \
                  % (mtxR_fx, mtxR_fy, mtxR_cx, mtxR_cy, mtxR_k1, mtxR_k2, mtxR_p1, mtxR_p2, mtxR_k3, mtxR_k4, mtxR_k5,
                     mtxR_k6, mtxL_fx, mtxL_fy,
                     mtxL_cx, mtxL_cy, mtxL_k1, mtxL_k2, mtxL_p1, mtxL_p2, mtxL_k3, mtxL_k4, mtxL_k5, mtxL_k6, Rx, Ry,
                     Rz, Tx, Ty, Tz, bin_file)

            print(cmd)
        self.process = QtCore.QProcess()

        self.process.start(cmd)
        self.process.readyReadStandardOutput.connect(
            lambda: self.read_result(str(self.process.readAllStandardOutput().data().decode('utf-8'))))
        self.process.waitForFinished()
        time.sleep(3)
        self.check_eeprom_write_process()
        self.process.kill()

    def Thread_Left_Camera(self):
        show_video_flag=False

        if self.cam_cfg['camera']['calibrate_type'] == "stereo":
            ret_left, self.frame_left = self.camera.read()
            ret_right, self.frame_right = self.camera.read_1()
            if ret_left and ret_right:
                show_video_flag=True
                self.frame_left = cv2.cvtColor(self.frame_left, cv2.COLOR_BGR2RGB)
                self.frame_right = cv2.cvtColor(self.frame_right, cv2.COLOR_BGR2RGB)
                rgbImage = np.hstack([self.frame_left, self.frame_right])
        else:
            show_video_flag = True
            ret_left, self.frame_left = self.camera.read()
            if ret_left:
                self.frame_left = cv2.cvtColor(self.frame_left, cv2.COLOR_BGR2RGB)
                rgbImage=self.frame_left

        if show_video_flag:
            try:
                Qimg = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],rgbImage.shape[1] * 3,QImage.Format_RGB888).rgbSwapped()  # Convert array to QImage
                Pixmap = QPixmap.fromImage(Qimg)
                width = self.centralwidget.width()
                height = self.centralwidget.height()
                self.Videolabel.resize(width, height)
                self.Videolabel.setScaledContents(True)
                self.Videolabel.setPixmap(Pixmap)
            except Exception as err:
                print(err)


    def checkFileNumber(self,folder):
        lambdaLen=lambda file:len(os.listdir(file))
        return lambdaLen(folder)

    def calibrateProcess(self):
        thread_calibration = threading.Thread(target=self.calibration_opencv)
        thread_calibration.start()
        #thread_calibration.join()

    def calibration_opencv(self):
        self.sn_number=self.snlineEdit.text()
        if self.sn_number == "":
            QMessageBox.information(self, 'warning', 'please scan sn number')
            return

        save_result = os.path.join(self.sn_number, "result")
        pic_img_path = self.sn_number

        global FLAG
        global dict_left_calibrate_pic_error
        global dict_right_calibrate_pic_error
        dict_left_calibrate_pic_error.clear()
        dict_right_calibrate_pic_error.clear()

        if self.cam_cfg['camera']['calibrate_type']!="stereo":
            print("=========== start singel camera calibrte  =========")
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 71, 1e-6)
            flag_left_calibration = 0
            if self.cam_cfg['camera']['calibrate_type'] == "fisheye":
                objp = np.zeros((1, self.chessboard_height * self.chessboard_with, 3),
                                np.float32)  # I used a 10×16 checkerboard, and you could modify the relevant parameters according to your checkerboard
                objp[0, :, :2] = np.mgrid[0:self.chessboard_with, 0:self.chessboard_height].T.reshape(-1, 2)
                # If the following parameters are used, 8 deformation parameters will be used, K4,K5, and K6 will be activated
                flag_left_calibration |= cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC
                flag_left_calibration |= cv2.fisheye.CALIB_FIX_SKEW
            else:
                flag_left_calibration |= cv2.CALIB_RATIONAL_MODEL
                objp = np.zeros((self.chessboard_height * self.chessboard_with, 3),
                                np.float32)  # I used a 10×16 checkerboard, and you could modify the relevant parameters according to your checkerboard
                objp[:, :2] = np.mgrid[0:self.chessboard_with, 0:self.chessboard_height].T.reshape(-1, 2)

            objpoints = []  # 3d points in real world space

            imgpointsL = []

            if (not os.path.exists(save_result)):
                os.makedirs(save_result)

            # img_right_path = save_result+'/right/*.jpg'
            if not os.path.exists(pic_img_path):
                QMessageBox.information(self, 'warning', 'no storage pictures path exist')
                return

            img_left_path = pic_img_path + '/*.jpg'
            # images_right = glob.glob(img_right_path)
            # images_right.sort()
            # img_show_righ_path = images_right[0]
            images_left = glob.glob(img_left_path)
            if len(images_left) == 0:
                QMessageBox.information(self, 'warning', 'no storage pictures  exist')
                return
            images_left.sort()
            print(images_left)
            img_show_left_path = images_left[0]

            find_left_file = []

            for fname_left in images_left:
                ChessImaL = cv2.imread(fname_left)  # The left view
                ChessImaL_gray = cv2.cvtColor(ChessImaL, cv2.COLOR_BGR2GRAY)
                flag_left = 0
                flag_left = cv2.CALIB_CB_ADAPTIVE_THRESH  # cv2.CALIB_CB_NORMALIZE_IMAGE
                flag_left |= cv2.CALIB_CB_FAST_CHECK
                flag_left |= cv2.CALIB_CB_NORMALIZE_IMAGE

                retL, cornersL = cv2.findChessboardCorners(ChessImaL, (self.chessboard_with, self.chessboard_height),
                                                           flags=flag_left)  # Extract the corners of each image on the left


                if True == retL:
                    # cornersL=cv2.resize(cornersL,(int(self.pic_width), int(self.pic_height)))
                    print("pic %s  found corners" % fname_left)
                    objpoints.append(objp)
                    cv2.cornerSubPix(ChessImaL_gray, cornersL, (11, 11), (-1, -1),
                                     criteria)  # Subpixel precision, the rough extraction of the corner of the precision
                    find_left_file.append(fname_left)
                    # find_right_file.append(fname_right)
                    # imgpointsR.append(cornersR)
                    imgpointsL.append(cornersL)
                    # print(cornersL)
                    # print(type(cornersL))
                else:
                    print("##pic %s not found corners" % fname_left)

            if len(imgpointsL) == 0:
                QMessageBox.information(self, 'error', 'no pictures find corners')
                return

            N_OK = len(objpoints)
            mean_error_left = 0
            if self.cam_cfg['camera']['calibrate_type'] == "fisheye":
                mtxL = np.zeros((3, 3))
                distL = np.zeros((4, 1))

                retL, _, _, rvecsL, tvecsL = cv2.fisheye.calibrate(
                    objpoints, imgpointsL, ChessImaL_gray.shape[::-1], mtxL,
                    distL, None, None, flags=flag_left_calibration, criteria=criteria)

                for i in range(len(imgpointsL)):
                    imgpoints2, _ = cv2.fisheye.projectPoints(objpoints[i], rvecsL[i], tvecsL[i], mtxL, distL)
                    img_list = []
                    for t in range(len(imgpointsL[i])):
                        img_list.append(imgpointsL[i][t].tolist())
                    img_point_list = []
                    for img_point in img_list:
                        img_point_list.append(img_point[0][0])
                        img_point_list.append(img_point[0][1])
                    imgpoints_list = []
                    for imgpoint in imgpoints2.tolist()[0]:
                        imgpoints_list.append(imgpoint[0])
                        imgpoints_list.append(imgpoint[1])

                    err = 2 * cv2.norm(np.array(img_point_list), np.array(imgpoints_list), cv2.NORM_L2) / len(
                        imgpoints_list)

                    print("left pic:{0},error:{1}".format(find_left_file[i], err))
                    dict_left_calibrate_pic_error[find_left_file[i]] = str(err)
                    mean_error_left += err
                mean_reproject_error_left = mean_error_left / len(imgpointsL)
                print("left reproject error  : ", mean_reproject_error_left)

                # print('mean reproject error', (mean_reproject_error_left + mean_reproject_error_right) / 2)

                hL, wL = ChessImaL.shape[:2]
                frameL = cv2.imread(img_show_left_path)
                map1, map2 = cv2.fisheye.initUndistortRectifyMap(mtxL, distL, np.eye(3), mtxL, (wL, hL), cv2.CV_16SC2)
                # dst = cv2.undistort(frameL, mtxL, distL, None, None)
                dst = cv2.remap(frameL, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                cv2.imwrite(save_result + '/correct.jpg', dst)

                dst_list = []
                for i in range(distL.shape[0]):
                    for j in range(distL.shape[1]):
                        dst_list.append(distL[i][j])

                with open(save_result + "/calibrate.txt", 'w') as f:
                    f.write('mtxL :: ' + '\n')
                    for i in range(mtxL.shape[0]):
                        if i == 0:
                            f.write("[[")
                        else:
                            f.write(" [")
                        for j in range(mtxL.shape[1]):
                            f.write(str(mtxL[i][j]) + " ")
                        if i == 2:
                            f.write("]]")
                        else:
                            f.write("]")
                        f.write('\n')
                    f.write('distL :: ' + '\n')
                    f.write("[")
                    for dst_item in dst_list:
                        f.write(str(dst_item) + " ")
                    f.write("]")
                    f.write('\n')

                    f.write("left reproject error  :  " + str(mean_reproject_error_left) + '\n')
            else:
                retL, mtxL, distL, rvecsL, tvecsL, stdDeviationsIntrinsics_L, stdDeviationsExtrinsics_L, perViewErrors_L = cv2.calibrateCameraExtended(
                    objpoints, imgpointsL, ChessImaL_gray.shape[::-1], None, None, flags=flag_left_calibration,
                    criteria=criteria)
                for i in range(len(objpoints)):
                    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsL[i], tvecsL[i], mtxL, distL)
                    error = cv2.norm(imgpointsL[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                    print("left pic:{0},error:{1}".format(find_left_file[i], error))
                    dict_left_calibrate_pic_error[find_left_file[i]] = str(error)
                    mean_error_left += error
                mean_reproject_error_left = mean_error_left / len(objpoints)
                print("left reproject error  : ", mean_reproject_error_left)
                frameL = cv2.imread(img_show_left_path)
                Left_Stereo_Map = cv2.undistort(frameL, mtxL, distL, None, mtxL)

                cv2.imwrite(save_result + '/correct.jpg', Left_Stereo_Map)
                with open(save_result + "/calibrate.txt", 'w') as f:
                    f.write('mtxL :: ' + '\n')
                    for i in range(mtxL.shape[0]):
                        if i == 0:
                            f.write("[[")
                        else:
                            f.write(" [")
                        for j in range(mtxL.shape[1]):
                            f.write(str(mtxL[i][j]) + " ")
                        if i == 2:
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
                    f.write("left reproject error  :  " + str(mean_reproject_error_left) + '\n')
            dict_left_calibrate_pic_error[os.path.join(save_result, "correct.jpg")] = "0.0000"
        else:
            print("start stereo calibrate")
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
            objp = np.zeros((self.chessboard_height * self.chessboard_with, 3),
                            np.float32)  # I used a 10×16 checkerboard, and you could modify the relevant parameters according to your checkerboard
            objp[:, :2] = np.mgrid[0:self.chessboard_with, 0:self.chessboard_height].T.reshape(-1, 2)
            objpoints = []  # 3d points in real world space
            imgpointsR = []  # 2d points in image plane
            imgpointsL = []

            if (not os.path.exists(save_result)):
                os.makedirs(save_result)

            img_right_path = self.sn_number + '/right/*.jpg'
            img_left_path = self.sn_number+ '/left/*.jpg'
            images_right = glob.glob(img_right_path)
            images_right.sort()
            img_show_righ_path = images_right[0]
            images_left = glob.glob(img_left_path)
            images_left.sort()
            img_show_left_path = images_left[0]

            if len(images_left) != len(images_right):
                QMessageBox.information(self, "Message",
                                        "length of left is {0} is not equal to length of right {1}".format(
                                            len(images_left), len(images_right)))
                return

            find_right_file = []
            find_left_file = []

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
                retR, cornersR = cv2.findChessboardCorners(ChessImaR_gray, (self.chessboard_with, self.chessboard_height), None,
                                                           flags=flag_right)  # Extract the corners of each image on the right

                retL, cornersL = cv2.findChessboardCorners(ChessImaL_gray, (self.chessboard_with, self.chessboard_height), None,
                                                           flags=flag_left)  # Extract the corners of each image on the left
                if not retL or not retR:
                    dict_left_calibrate_pic_error[fname_left] = "no find"
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
                objpoints, imgpointsR, ChessImaR_gray.shape[::-1], None, None, flags=flag_right_calibaration,
                criteria=criteria)

            #   Subsequent to get new camera matrix initUndistortRectifyMap to generate mapping relationship with remap
            hR, wR = ChessImaR.shape[:2]
            OmtxR, roiR = cv2.getOptimalNewCameraMatrix(mtxR, distR, (wR, hR), 1, (wR, hR))
            flag_left_calibration = 0
            # If the following parameters are used, 8 deformation parameters will be used, K4,K5, and K6 will be activated
            flag_left_calibration |= cv2.CALIB_RATIONAL_MODEL
            # Calibrate the left camera separately
            retL, mtxL, distL, rvecsL, tvecsL, stdDeviationsIntrinsics_L, stdDeviationsExtrinsics_L, perViewErrors_L = cv2.calibrateCameraExtended(
                objpoints, imgpointsL, ChessImaL_gray.shape[::-1], None, None, flags=flag_left_calibration,
                criteria=criteria)

            mean_error_right = 0
            print("len(objpoints)=", len(objpoints))
            for i in range(len(objpoints)):
                imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsR[i], tvecsR[i], mtxR, distR)
                error = cv2.norm(imgpointsR[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                print("right pic:{0},error:{1}".format(find_right_file[i], error))
                dict_right_calibrate_pic_error[find_right_file[i]] = str(error)
                mean_error_right += error
            mean_reproject_error_right = mean_error_right / len(objpoints)
            print("right reproject error : ", mean_reproject_error_right)

            mean_error_left = 0
            for i in range(len(objpoints)):
                imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsL[i], tvecsL[i], mtxL, distL)
                error = cv2.norm(imgpointsL[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                print("left pic:{0},error:{1}".format(find_left_file[i], error))
                dict_left_calibrate_pic_error[find_left_file[i]] = str(error)
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
            retS, MLS, dLS, MRS, dRS, R, T, E, F, perViewErrors = cv2.stereoCalibrateExtended(objpoints, imgpointsL,
                                                                                              imgpointsR,
                                                                                              mtxL, distL, mtxR, distR,
                                                                                              ChessImaR_gray.shape[
                                                                                              ::-1], None,
                                                                                              None, criteria=criteria,
                                                                                              flags=flags_two)
            print('retS', retS)
            print('distL', distL)
            print('dLS', dLS)
            print('distR', distR)
            print('dRS', dRS)
            # print('perViewErrors', perViewErrors)
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
            # frameR = cv2.imread("char_left.jpg")
            # frameL = cv2.imread("char_right.jpg")
            Left_rectified = cv2.remap(frameL, Left_Stereo_Map[0], Left_Stereo_Map[1], cv2.INTER_LANCZOS4,
                                       cv2.BORDER_CONSTANT,
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
            img_compare.paste(im_R, box=(im_L.size[0], 0))
            # Line evenly an image that has been pole-aligned
            save_img = np.array(img_compare)
            for i in range(1, 20):
                h_len = int(height / 20)
                cv2.line(save_img, (0, i * h_len), (width, i * h_len), (0, 0, 255), 2)
            cv2.imwrite(save_result + '/two.jpg', save_img)
            # save_data = './result'
            # if not os.path.exists(save_data):
            #    os.mkdir(save_data)
            R = cv2.Rodrigues(R)[0]
            print(str(R))
            with open(save_result + "/calibrate.txt", 'w') as f:
                f.write('retR :: ' + str(retR) + '\n')
                f.write('mtxR :: ' + '\n')
                for i in range(mtxR.shape[0]):
                    if i == 0:
                        f.write("[[")
                    else:
                        f.write(" [")
                    for j in range(mtxR.shape[1]):
                        f.write(str(mtxR[i][j]) + " ")
                    if i == 2:
                        f.write("]]")
                    else:
                        f.write("]")
                    f.write('\n')
                # f.write(str(mtxR))
                # f.write('\n')
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
                # f.write(str(mtxL))
                for i in range(mtxL.shape[0]):
                    if i == 0:
                        f.write("[[")
                    else:
                        f.write(" [")
                    for j in range(mtxL.shape[1]):
                        f.write(str(mtxL[i][j]) + " ")
                    if i == 2:
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

                # f.write(str(R))

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
                f.write("mean reproject error  :  " + str(
                    (mean_reproject_error_left + mean_reproject_error_right) / 2) + '\n')
        print("============ calibrate ending ======================")
        print(dict_left_calibrate_pic_error)
        FLAG = True

    def captureImageProcess(self):
        folder=self.snlineEdit.text()
        if folder == "":
            print("sn is null")
            return
        if not os.path.exists(folder):
            os.makedirs(folder)

        img_left_path=""
        img_right_path=""
        if self.cam_cfg['camera']['calibrate_type'] == "stereo":
            if not os.path.exists(os.path.join(folder, "left")):
                os.makedirs(os.path.join(folder, "left"))
            if not os.path.exists(os.path.join(folder, "right")):
                os.makedirs(os.path.join(folder, "right"))

            count=self.checkFileNumber(os.path.join(folder, "left"))
            img_left_path = os.path.join(folder, "left","%03d.jpg"%count)
            img_right_path = os.path.join(folder, "right", "%03d.jpg" % count)
        else:
            count = self.checkFileNumber(folder)
            img_left_path = os.path.join(folder,"%03d.jpg"%count)
            #file_name=os.path.join(folder,"%03d.jpg"%count)

        global CAPTURE_FLAG
        CAPTURE_FLAG = True
        global capture_path
        # global frame_left
        capture_path = img_left_path
        # frame_left=cv2.resize(frame_left,(1920,1200),interpolation=cv2.INTER_AREA)
        cv2.imwrite(img_left_path, self.frame_left)
        self.ch.additems()
        if self.cam_cfg['camera']['calibrate_type'] == "stereo":
            # if self.cap_right.isOpened() == True:
            global RIGHT_CAPTURE_FLAG
            RIGHT_CAPTURE_FLAG = True
            global right_capture_path
            # global frame_right
            right_capture_path = img_right_path
            # frame_right = cv2.resize(frame_right, (1920, 1200), interpolation=cv2.INTER_AREA)
            cv2.imwrite(img_right_path, self.frame_right)
            self.ch.additems()



    @QtCore.pyqtSlot(QPixmap)
    def display_to_label(self, pixelmap):
        #print("display to label")
        width = self.centralwidget.width()
        height = self.centralwidget.height()
        self.Videolabel.resize(width, height)
        self.Videolabel.setScaledContents(True)
        self.Videolabel.setPixmap(pixelmap)





