# from PyQt5.QtGui import *

# from PyQt5.QtGui import Qt
# from PyQt5.QtCore import *
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (
    QDialogButtonBox,
    QProgressBar,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QDialog,
)


import time
import datetime
import json
import cv2
import numpy as np

from libs.utils import newIcon

BB = QDialogButtonBox


class Worker(QThread):
    progressBarValue = pyqtSignal(int)
    listValue = pyqtSignal(str)
    endsignal = pyqtSignal(int, str)
    handle = 0

    def __init__(self, ocr, mImgList, mainThread, model):
        super(Worker, self).__init__()
        self.ocr = ocr
        self.mImgList = mImgList
        self.mainThread = mainThread
        self.model = model
        self.setStackSize(1024 * 1024)

    def extract_output(self, result_easyocr):
        result_dic = list()
        for result in result_easyocr:
            posi = [[float(i[0]), float(i[1])] for i in result[0]]
            chars = result[1]
            cond = result[2]
            result_dic.append([posi, (chars, cond)])
        return result_dic

    def run(self):
        try:
            findex = 0
            for Imgpath in self.mImgList:
                if self.handle == 0:
                    self.listValue.emit(Imgpath)
                    if self.model == "paddle":
                        h, w, _ = cv2.imdecode(
                            np.fromfile(Imgpath, dtype=np.uint8), 1
                        ).shape
                        if h > 12 and w > 12:
                            result_easyocr = self.ocr.readtext(Imgpath)
                            self.result_dic = self.extract_output(result_easyocr)
                        else:
                            print(
                                "The size of", Imgpath, "is too small to be recognised"
                            )
                            self.result_dic = None

                    # 结果保存
                    if self.result_dic is None or len(self.result_dic) == 0:
                        print("Can not recognise file", Imgpath)
                        pass
                    else:
                        strs = ""
                        for res in self.result_dic:
                            chars = res[1][0]
                            cond = res[1][1]
                            posi = res[0]
                            strs += (
                                "Transcription: "
                                + chars
                                + " Probability: "
                                + str(cond)
                                + " Location: "
                                + json.dumps(posi)
                                + "\n"
                            )
                        # for res in self.result_dic:

                        #     posi = [[float(i[0]), float(i[1])] for i in res[0]]
                        #     chars = res[1]
                        #     cond  = res[2]
                        #     strs += "Transcription: " + chars + " Probability: " + str(cond) + \
                        #             " Location: " + json.dumps(posi) +'\n'
                        # Sending large amounts of data repeatedly through pyqtSignal may affect the program efficiency
                        self.listValue.emit(strs)
                        self.mainThread.result_dic = self.result_dic
                        self.mainThread.filePath = Imgpath
                        # 保存
                        self.mainThread.saveFile(mode="Auto")
                    findex += 1
                    self.progressBarValue.emit(findex)
                else:
                    break
            self.endsignal.emit(0, "readAll")
            self.exec()
        except Exception as e:
            print(e)
            raise


class AutoDialog(QDialog):

    def __init__(
        self, text="Enter object label", parent=None, ocr=None, mImgList=None, lenbar=0
    ):
        super(AutoDialog, self).__init__(parent)
        self.setFixedWidth(1000)
        self.parent = parent  # type: ignore
        self.ocr = ocr
        self.mImgList = mImgList
        self.lender = lenbar
        self.pb = QProgressBar()
        self.pb.setRange(0, self.lender)
        self.pb.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.pb)
        self.model = "paddle"
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)

        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Orientation.Horizontal, self)
        bb.button(BB.Ok).setIcon(newIcon("done"))  # type: ignore
        bb.button(BB.Cancel).setIcon(newIcon("undo"))  # type: ignore
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        bb.button(BB.Ok).setEnabled(False)  # type: ignore

        self.setLayout(layout)
        # self.setWindowTitle("自动标注中")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # self.setWindowFlags(Qt.WindowCloseButtonHint)

        self.thread_1 = Worker(self.ocr, self.mImgList, self.parent, "paddle")
        self.thread_1.progressBarValue.connect(self.handleProgressBarSingal)
        self.thread_1.listValue.connect(self.handleListWidgetSingal)
        self.thread_1.endsignal.connect(self.handleEndsignalSignal)
        self.time_start = time.time()  # save start time

    def handleProgressBarSingal(self, i):
        self.pb.setValue(i)

        # calculate time left of auto labeling
        avg_time = (
            time.time() - self.time_start
        ) / i  # Use average time to prevent time fluctuations
        time_left = str(datetime.timedelta(seconds=avg_time * (self.lender - i))).split(
            "."
        )[
            0
        ]  # Remove microseconds
        self.setWindowTitle("EasyOCRLabel  --  " + f"Time Left: {time_left}")  # show

    def handleListWidgetSingal(self, i):
        self.listWidget.addItem(i)
        titem = self.listWidget.item(self.listWidget.count() - 1)
        self.listWidget.scrollToItem(titem)

    def handleEndsignalSignal(self, i, str):
        if i == 0 and str == "readAll":

            bb_button_ok: Optional[QPushButton] = self.buttonBox.button(BB.Ok)
            if bb_button_ok is None:
                raise ValueError("bb_button_ok")
            bb_button_ok.setEnabled(True)

            bb_button_cancel = self.buttonBox.button(BB.Cancel)
            if bb_button_cancel is None:
                raise ValueError("bb_button_cancel")
            bb_button_cancel.setEnabled(False)

    def reject(self):
        print("reject")
        self.thread_1.handle = -1
        self.thread_1.quit()
        # del self.thread_1
        # if self.thread_1.isRunning():
        #     self.thread_1.terminate()
        # self.thread_1.quit()
        # super(AutoDialog,self).reject()
        while not self.thread_1.isFinished():
            pass
        self.accept()

    def validate(self):
        self.accept()

    def postProcess(self):
        try:
            self.edit.setText(self.edit.text().trimmed())
            # print(self.edit.text())
        except AttributeError:
            # PyQt5: AttributeError: 'str' object has no attribute 'trimmed'
            self.edit.setText(self.edit.text())
            print(self.edit.text())

    def popUp(self):
        self.thread_1.start()
        return 1 if self.exec_() else None

    def closeEvent(self, event):
        print("???")
        # if self.thread_1.isRunning():
        #     self.thread_1.quit()
        #
        #     # self._thread.terminate()
        # # del self.thread_1
        # super(AutoDialog, self).closeEvent(event)
        self.reject()
