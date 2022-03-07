import cv2

from argusCamera import ArgusCamera

if __name__ =="__main__":
    camera = ArgusCamera(0, previewWidth=1920, previewheight=1200, previewPosX=100, previewPosY=100, captureWidth=1920,
                         captureHeight=1200, rotation=180)
    while True:
        ret_left, frame_left = camera.read()
        ret_right, frame_right = camera.read_1()
        if ret_left:
            cv2.imshow("left_video",frame_left)
            cv2.waitKey(1)
        if ret_right:
            cv2.imshow("right_video", frame_right)
            cv2.waitKey(1)