实现功能：
1.nvidia平台单目双目的标定，可改配置文件兼容不同的标定方法
{
    "camera": {
        "device_name": "max96712",
        "i2c_addr": "0x54",
        "cam_index": 0,
        "reso_h": 1200,
        "reso_w": 1920,
        "board_type": 0,
        "board_size_h": 10,
        "board_size_w": 16,
        "calibrate_type": "stereo"
    }
}
calibrate_type 支持stereo,fisheye,single
run app:
    python3 main.py
	