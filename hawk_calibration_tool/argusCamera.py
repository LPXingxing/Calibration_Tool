# argusCamera.py
# 
# The interface to libargus
# 
# It has preview video on the screen through libargus low level library
# and capture images at the same time
#   
# 
# Leopard Imaging, Inc 2020
# 

import ctypes
import numpy as np
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARGUS_DANYMIC_LIBRARY = os.path.join(BASE_DIR, '_argusCamera.so')

# String overlay class
#    holds the text, position and color
class ArgusStrOverlay:
    def __init__(self, text, pos, color):
        self.text = text     # text 
        self.pos = pos       # position (x,y)
        self.color = color   # 0x00rrggbb : rr: red, gg: green, bb: blue

# Rectangle overaly class
#   holds the position, size and color
class ArgusRectOverlay:
    def __init__(self, pos, size, color):
        self.pos = pos       # position (x,y)
        self.size = size     # size (w, h)
        self.color = color   # 0x00rrggbb : rr: red, gg: green, bb: blue

# Argus Camera Interface
#  it calls functions from dynamic link library (_argusCamera.so)
#  the library is based on Nvidia Multimedia API
class ArgusCamera:
    def __init__(self, port, previewWidth=960, previewheight=540,
                captureWidth=640, captureHeight=480,gain=0,exposure_time=0):
        # port : camera port
        # previewWidth : privew window width
        # previewHeight : preview window height
        # previewPosX : preview window start position X
        # previewPosY : preview window start position Y
        # captureWidth : capture image width
        # captureHeight : capture image height
        # argus_direct_display : not used yet, TBD
        # rotation : rotate the image, available options are: 0, 90, 180, 270 degree
        #cap = ArgusCamera(0, previewWidth=1920, previewheight=1200, previewPosX=100, previewPosY=100, captureWidth=1920,
        #                  captureHeight=1200, rotation=180, exposure_time=exposure_time)

        self.__port = port
        self.__captureWidth = captureWidth
        self.__captureHeight = captureHeight
        self.count=1
        self.__camera = ctypes.CDLL(ARGUS_DANYMIC_LIBRARY)

        print("exposure_time={0}",format(exposure_time))
        self.__camera.argusCaptureDisplay(
            ctypes.c_int(port),
            ctypes.c_int(previewWidth), ctypes.c_int(previewheight),
            ctypes.c_int(captureWidth), ctypes.c_int(captureHeight),
            ctypes.c_int(30), # fixed to 30fps for now
            ctypes.c_int(gain),
            ctypes.c_int(exposure_time))

    # return a cv2 image frame
    def read(self):
        try:
            # create a frame to fill in date and return
            frame = np.zeros((self.__captureWidth * self.__captureHeight*4,), dtype=np.uint8)

            # capture a buffer in jpeg format, time out 1 second
            # ret is the jpeg buffer size
            ret = self.__camera.argusGetBuffer(ctypes.c_void_p(frame.ctypes.data),
                        ctypes.c_int(1000))

            if ret != 0:
                # decode jpeg data to an image frame
                cv2Frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                #print("ret=%d"%ret) 
                # convert BGRA to BGR
                #rgb_data = frame.reshape(self.__captureHeight, self.__captureWidth, 4)
                #cv2Frame = cv2.cvtColor(rgb_data, cv2.COLOR_BGRA2RGB)
                #cv2Frame = cv2.cvtColor(rgb_data, cv2.COLOR_YUV2BGR_NV21);
                #jpg_name="output_%d.jpg"%self.count
                #self.count+=1
                #cv2.imwrite(jpg_name,cv2Frame)
                return True, cv2Frame
            else:
                print("catpure time out")

        except Exception as err:
            #pass
            #pass
            print('ArgusCamera capture error,{0}'.format(err))

        return False,0
    
    def read_1(self):
        try:
            frame = np.zeros((self.__captureWidth * self.__captureHeight*4,), dtype=np.uint8)
            ret = self.__camera.argusGetBuffer_1(ctypes.c_void_p(frame.ctypes.data),
                                            ctypes.c_int(1000))
            if ret!=0:
                cv2Frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                return True,cv2Frame
            else:
                print("capture_1 time out")
        except Exception as err:
            print('ArgusCamera_1 capture error,{0}'.format(err))

        return False,0
    

    # set overlay text messages
    def setText(self, strOverlayText):
        if len(strOverlayText) == 0:  # to clear the text
            # create byte objects from the strings
            b_string = " ".encode('utf-8')

            self.__camera.argusSetOverlayText(
                ctypes.c_char_p(b_string),
                ctypes.c_uint(0),
                ctypes.c_uint(0),
                ctypes.c_ulong(0),
                ctypes.c_int(0),
                ctypes.c_int(0) 
            )
        else:    
            for count, item in enumerate(strOverlayText):

                # create byte objects from the strings
                b_string = item.text.encode('utf-8')

                self.__camera.argusSetOverlayText(
                    ctypes.c_char_p(b_string),
                    ctypes.c_uint(item.pos[0]),
                    ctypes.c_uint(item.pos[1]),
                    ctypes.c_ulong(item.color),
                    ctypes.c_int(count),
                    ctypes.c_int(count + 1) 
                )

    # set overlay rectangles
    def setRect(self, strOverlayRect):
        if len(strOverlayRect) == 0:  # to clear the rectangles
            self.__camera.argusSetOverlayRect(
                ctypes.c_uint(0),
                ctypes.c_uint(0),
                ctypes.c_uint(0),
                ctypes.c_uint(0),
                ctypes.c_ulong(0),
                ctypes.c_int(0),
                ctypes.c_int(0) ) 
        else:
            for count, item in enumerate(strOverlayRect):
                self.__camera.argusSetOverlayRect(
                    ctypes.c_uint(item.pos[0]),
                    ctypes.c_uint(item.pos[1]),
                    ctypes.c_uint(item.size[0]),
                    ctypes.c_uint(item.size[1]),
                    ctypes.c_ulong(item.color),
                    ctypes.c_int(count),
                    ctypes.c_int(count + 1) 
                )

    # call this function to release the resources
    def close(self):
        print("close camera")
        self.__camera.argusRelease()

    def release(self):
        self.__camera.argusRelease()
