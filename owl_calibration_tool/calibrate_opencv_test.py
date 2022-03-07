import cv2
import numpy as np
import os
from PIL import ImageQt
from PIL import Image
import glob

def calibration_opencv():
    sn_number = "N08410008"

    print("=========== start calibrte  =========")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
    objp = np.zeros((10 * 16, 3),
                    np.float32)  # I used a 10×16 checkerboard, and you could modify the relevant parameters according to your checkerboard
    objp[:, :2] = np.mgrid[0:16, 0:10].T.reshape(-1, 2)
    objpoints = []  # 3d points in real world space
    imgpointsR = []  # 2d points in image plane
    imgpointsL = []

    save_result=os.path.join(sn_number,"result")
    if (not os.path.exists(save_result)):
        os.makedirs(save_result)

    img_right_path = sn_number + '/right/*.jpg'
    img_left_path = sn_number + '/left/*.jpg'
    images_right = glob.glob(img_right_path)
    images_right.sort()
    img_show_righ_path = images_right[0]
    images_left = glob.glob(img_left_path)
    images_left.sort()
    img_show_left_path = images_left[0]

    if len(images_left) != len(images_right):
        print("length of left is {0} is not equal to length of right {1}".format(len(images_left),
                                                                                                   len(images_right)))
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
        retR, cornersR = cv2.findChessboardCorners(ChessImaR_gray, (16, 10), None,
                                                   flags=flag_right)  # Extract the corners of each image on the right

        retL, cornersL = cv2.findChessboardCorners(ChessImaL_gray, (16, 10), None,
                                                   flags=flag_left)  # Extract the corners of each image on the left
        if not retL or not retR:
            pass
            #dict_left_calibrate_pic_error[fname_left] = "no find"
            #dict_right_calibrate_pic_error[fname_right] = "no find"

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
        print("right pic:{0},error:{1}".format(find_right_file[i], error))
        #dict_right_calibrate_pic_error[find_right_file[i]] = str(error)
        mean_error_right += error
    mean_reproject_error_right = mean_error_right / len(objpoints)
    print("right reproject error : ", mean_reproject_error_right)

    mean_error_left = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecsL[i], tvecsL[i], mtxL, distL)
        error = cv2.norm(imgpointsL[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        print("left pic:{0},error:{1}".format(find_left_file[i], error))
        #dict_left_calibrate_pic_error[find_left_file[i]] = str(error)
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
        f.write("mean reproject error  :  " + str((mean_reproject_error_left + mean_reproject_error_right) / 2) + '\n')
    print("============ calibrate ending ======================")
    FLAG = True


calibration_opencv()