
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QPixmap
import time
import window
import sys
import os
import cv2
from Navgator import Nav

import time



class MainApp(QtWidgets.QMainWindow, window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pushButton.clicked.connect(self.load_len_matrix)
        self.pushButton_2.clicked.connect(self.load_capable)
        self.pushButton_3.clicked.connect(self.load_request)

        self.pushButton_4.clicked.connect(self.openDocs)

        self.pushButton_6.clicked.connect(self.procc_req)
        self.pushButton_5.clicked.connect(self.select_save)

    def select_save(self):
        self.path_to_save_ = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder','.')
        print(self.path_to_save_)

    def openDocs(self):
        try:
            os.startfile(os.getcwd() + '\\read.txt')
        except Exception as e:
            print(e)

    def load_len_matrix(self):
        self.roads_path, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   'Open Roads File', 'temp4/')
        self.label.setText("Файл: " + os.path.basename(self.roads_path))
        print(self.roads_path)

    def load_capable(self):
        self.capable, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                'Open Capable File', 'temp4/')
        self.label_2.setText("Файл: " + os.path.basename(self.capable))
        print(self.capable)

    def load_request(self):
        self.request, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                'Open Capable File', 'temp4/')
        self.label_3.setText("Файл: " + os.path.basename(self.request))
        print(self.request)

    def procc_req(self):
        try:
            if not self.lineEdit.text():
                self.rad = 5000
            else:
                self.rad = int(self.lineEdit.text())

            if all([self.request, self.capable, self.roads_path,
                    self.path_to_save_, self.rad]):
                    
                start_time = time.time()
                n = Nav(self.roads_path, self.capable,self.request, 
                              self.path_to_save_, self.rad)
                t2 = time.time() - start_time

                self.label_10.setText('Время обработки: ' + str(t2)[:10] + ' c.')

                path_s = '-'.join(n.min_path)
                self.label_12.setText(str(n.amount_of_all_paths))
                #self.label_14.setText(str(len(n.checked_paths)))
                self.label_7.setText(path_s)
                self.label_8.setText('Пройденное расстояние: ' + str(n.min_len))

                image = cv2.imread(self.path_to_save_ + "/Graph.png")
                # image = cv2.resize(gr, (500, 500))
                image = QtGui.QImage(image, image.shape[1],
                                     image.shape[0], image.shape[1] * 3, QtGui.QImage.Format_RGB888)
                pix = QtGui.QPixmap(image)
                
                self.label_5.clear()
                self.label_5.setPixmap(pix)

                del n

            else:
                print('Заполнены не все данные')
        except Exception as E:
            print('Не все данные заполненые', E)


# p2 = Navigator('temp2/Zayavka.xlsx','temp2/Vozmozhnosti.xlsx','temp2/Matritsa_rasstoyanii_774.xlsx',500)

# n = Navigator('temp2/Zayavka.xlsx', 'temp2/Vozmozhnosti.xlsx', 'temp2/Matritsa_rasstoyanii_774.xlsx','C:/Users/usenk/Desktop/Project/Navigator/to_save',500)

app = QtWidgets.QApplication(sys.argv)
window = MainApp()
window.show()
app.exec_()
# n = Navigator('temp2/Zayavka.xlsx', 'temp2/Vozmozhnosti.xlsx', 'temp2/Matritsa_rasstoyanii_774.xlsx',
#                          'C:\\Users\\usenk\\Desktop\Project\\Navigator\\to_save', 500)
