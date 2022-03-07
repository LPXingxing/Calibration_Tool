import sys
import os
from PyQt5 import QtWidgets
from argparse import ArgumentParser
from running import camera_tool_setup


if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/calibrate_config.json")
    parser = ArgumentParser(description='Leopard Calibrate Tool for Production')
    parser.add_argument('-camera_config_file',
                       default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/calibrate_config.json"),
                       type=str, help='The camera config file with absolute full path')
    args = parser.parse_args()
    app = QtWidgets.QApplication([])
    window = camera_tool_setup(args)
    window.show()
    sys.exit(app.exec_())






















