from itertools import chain, combinations
import copy
import pandas as pd
import xlsxwriter
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QPixmap
import time
import window
import sys
import os
import cv2

import networkx as nx
import matplotlib.pyplot as plt


def k_from_val(v_search, d):
    for name, ind in d.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
        if ind == v_search:
            return name


class Base:
    def __init__(self, name, capacity, ci_col):
        self.name = name
        self.max_capacity = capacity

        self.current_mean = [0 for _ in range(ci_col)]

    def update_value(self, ind, value):
        empty = self.max_capacity[ind] - self.current_mean[ind]

        if value <= empty:
            self.current_mean[ind] += value
            return value

        elif value >= empty >= 1:
            self.current_mean[ind] += empty
            return empty
        else:
            return 0


class Navigator:
    def __init__(self, request_path, path_to_capactity, path_to_roads, path_for_save, radius) -> None:
        self.path_for_save = path_for_save
        self.radius = radius

        self.load_capacities(path_to_capactity)

        self.load_roads(path_to_roads)

        self.load_request(request_path)

        print(f'Запрос из {self.start_base}:')
        print(dict(zip(self.ci.keys(), self.requset)))

        self.get_all_paths(self.start_base)

        print('All pathes', len(self.all_paths))

        self.ch_paths()

        print('All check pathes', len(self.checked_paths))

        for path in self.checked_paths:
            path.insert(0, self.start_base)
            path.append(self.start_base)

        self.get_fastest_path()

    def load_roads(self, path_to_roads):
        df = pd.read_excel(path_to_roads)
        df = df.fillna(0)
        out = []
        bases_ok = []
        for row in df.itertuples():
            print(row)
            line = []
            if int(row[2]) <= self.radius:

                bases_ok.append(row[1])
            else:
                df = df.drop(row[0], 0)
            # for i in range(2,len(row)):
            #    line.append(row[i])
            # out.append(line)
        for c_name in df.columns:
            if c_name != 'Unnamed: 0' and c_name not in bases_ok:
                df = df.drop(c_name, 1)
        for row in df.itertuples():
            # print(row)
            line = []
            for i in range(2, len(row)):
                line.append(int(row[i]))
            out.append(line)
        # for i in out:
        #    print(i)
        print(df)
        # Проверка того, что матрица квадратная
        m = len(out)
        for line in out:
            if len(line) != m:
                raise ValueError

        # Создание graph_ind

        self.graph_ind = {}
        ind = 0
        for base in df.columns.values.tolist()[1:]:
            self.graph_ind[str(base)] = int(ind)
            ind += 1

        print('Кол-во всевозможных Баз исходя из roads', len(out))

        self.len_matrix = out

    def load_capacities(self, path_to_capactity):
        df = pd.read_excel(path_to_capactity)
        df = df.fillna(0)
        out = []
        bases_count = 0
        for row in df.itertuples():
            line = []
            for i in range(2, len(row)):
                line.append(row[i])
            out.append(line)
            bases_count += 1
        print('Кол-во всевозможных Си исходя из capactiy',
              len(row) - 2)  # Т.к в pd 0-ый элемент - индекс, 1-ый элемент - имя базы
        self.ci_col = len(row) - 2
        print('Кол-во всевозможных Баз исходя из capactiy', bases_count)

        self.ci = {}
        for ci_ in df.columns.values.tolist()[1:]:
            self.ci[ci_] = 0

        self.bases_capacity = out

    def load_request(self, path_to_request):
        df = pd.read_excel(path_to_request)
        df = df.fillna(0)

        for i in df['Тип СИ']:
            self.ci[i] += 1
        for v in df['База']:
            if v:
                self.start_base = str(int(v))

        self.requset = list(self.ci.values())

    def _powerset(self, list_name):
        s = list(list_name)
        return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))

    def get_all_paths(self, base):
        full_list = list(self.graph_ind.keys())
        start_point = int(self.graph_ind[str(base)])
        full_list.pop(start_point)
        paths = self._powerset(full_list)
        outputs = []
        for path in paths:
            path = list(path)
            path.insert(0, base)
            path.append(base)
            outputs.append(path)

        self.all_paths = outputs

    def ch_paths(self):
        cheched_paths = []

        for path_ind, path in enumerate(self.all_paths):
            request = copy.copy(self.requset)
            path.pop(0)
            path.pop(-1)
            bases = [Base(list(self.graph_ind.keys())[i], self.bases_capacity[i], self.ci_col) for i in
                     range(len(self.len_matrix))]
            for base in path:
                base_ind = self.graph_ind[base]
                curr_base = bases[base_ind]
                for ind, value in enumerate(request):
                    request[ind] -= curr_base.update_value(ind, value)

            flag = True
            for v in request:
                if v != 0:
                    flag = False
            if flag:
                cheched_paths.append(path)

        self.checked_paths = cheched_paths

    def get_path_len(self, path):
        path_len = 0
        for i in range(len(path) - 1):
            path_len += self.len_matrix[self.graph_ind[str(path[i])]][self.graph_ind[str(path[i + 1])]]

        return path_len

    def get_fastest_path(self):

        paths_lenghts = []
        for i in range(len(self.checked_paths)):
            paths_lenghts.append(self.get_path_len(self.checked_paths[i]))

        workbook = xlsxwriter.Workbook(self.path_for_save + '/output.xlsx')
        worksheet = workbook.add_worksheet()
        self.min_l = min(paths_lenghts)
        self.f_path = copy.copy(self.checked_paths[paths_lenghts.index(min(paths_lenghts))])
        print('Самый короткий путь: ', min(paths_lenghts), self.checked_paths[paths_lenghts.index(min(paths_lenghts))])
        worksheet.write('A1', 'Старт:' + str(self.start_base))
        worksheet.write('B1', 'Длина:' + str(min(paths_lenghts)))
        curr_line = 2
        path = self.checked_paths[paths_lenghts.index(min(paths_lenghts))]
        request = copy.copy(self.requset)
        path.pop(0)
        path.pop(-1)
        bases = [Base(list(self.graph_ind.keys())[i], self.bases_capacity[i], self.ci_col) for i in
                 range(len(self.len_matrix))]
        for base in path:
            base_ind = self.graph_ind[base]
            curr_base = bases[base_ind]
            for ind, value in enumerate(request):
                request[ind] -= curr_base.update_value(ind, value)
        # print('----------')
        for base in bases:

            if any(base.current_mean):
                worksheet.write(f'A{curr_line}', str(base.name))
                worksheet.write(f'B{curr_line}', f'Отгруженное количество Cи: {base.current_mean}')
                curr_line += 1
                # print(base.name, base.current_mean)

        workbook.close()


# p1 = Navigator('temp/request1.xlsx','temp/capacity.xlsx','temp/roads.xlsx')
#
# print(len(p1.all_paths))


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

        # self.path_to_save_ = 'C:/Users/usenk/Desktop/Project/Navigator/to_save'

    #
    # self.r = 500
    # self.roads_path, self.capable, self.request = 0, 0, 0
    #
    def select_save(self):
        self.path_to_save_ = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        print(self.path_to_save_)

    def openDocs(self):
        try:
            os.startfile(os.getcwd() + '\\read.txt')
        except Exception as e:
            print(e)

    def load_len_matrix(self):
        self.roads_path, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   'Open Roads File', 'temp2/')
        self.label.setText("Файл: " + os.path.basename(self.roads_path))
        print(self.roads_path)

    def load_capable(self):
        self.capable, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                'Open Capable File', 'temp2/')
        self.label_2.setText("Файл: " + os.path.basename(self.capable))
        print(self.capable)

    def load_request(self):
        self.request, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                'Open Capable File', 'temp2/')
        self.label_3.setText("Файл: " + os.path.basename(self.request))
        print(self.request)

    def procc_req(self):
        try:
            if not self.lineEdit.text():
                self.rad = 500
            else:
                self.rad = int(self.lineEdit.text())

            if all([self.request, self.capable, self.roads_path,
                                                     self.path_to_save_, self.rad]):
                start_time = time.time()
                n = Navigator(self.request, self.capable, self.roads_path,
                                                         self.path_to_save_, self.rad)

                t2 = time.time() - start_time

                self.label_10.setText('Время обработки: ' + str(t2)[:10] + ' c.')
                path_s = '-'.join(n.f_path)
                self.label_12.setText(str(len(n.all_paths)))
                self.label_14.setText(str(len(n.checked_paths)))
                self.label_7.setText(path_s)
                self.label_8.setText('Пройденное расстояние: ' + str(n.min_l))

                print('graph_ind', n.graph_ind)
                arr = n.len_matrix
                matrix_p = []
                for i in range(len(arr)):
                    for j in range(len(arr)):
                        if int(arr[i][j]) > 0:
                            c = [str(k_from_val(i, n.graph_ind)), str(k_from_val(j, n.graph_ind)), int(arr[i][j]) / 10000]
                            matrix_p.append(c)
                print(matrix_p)

                G = nx.DiGraph()
                G.add_weighted_edges_from(matrix_p)
                weights = nx.get_edge_attributes(G, 'weight')
                pos = nx.circular_layout(G)
                nx.draw_networkx(G, pos=pos, node_size=1000)
                nx.draw_networkx_edge_labels(G, pos, edge_labels=weights)
                plt.savefig(self.path_to_save_ + "/Graph.png", format="PNG")
                image = cv2.imread(self.path_to_save_ + "/Graph.png")
                #image = cv2.resize(gr, (500, 500))
                image = QtGui.QImage(image, image.shape[1],
                                     image.shape[0], image.shape[1] * 3, QtGui.QImage.Format_RGB888)
                pix = QtGui.QPixmap(image)
                self.label_5.setPixmap(pix)
            else:
                print('Заполнены не все данные')
        except Exception as E:
            print('Не все данные заполненые',E)


# p2 = Navigator('temp2/Zayavka.xlsx','temp2/Vozmozhnosti.xlsx','temp2/Matritsa_rasstoyanii_774.xlsx',500)

# n = Navigator('temp2/Zayavka.xlsx', 'temp2/Vozmozhnosti.xlsx', 'temp2/Matritsa_rasstoyanii_774.xlsx','C:/Users/usenk/Desktop/Project/Navigator/to_save',500)

app = QtWidgets.QApplication(sys.argv)
window = MainApp()
window.show()
app.exec_()
# n = Navigator('temp2/Zayavka.xlsx', 'temp2/Vozmozhnosti.xlsx', 'temp2/Matritsa_rasstoyanii_774.xlsx',
#                          'C:\\Users\\usenk\\Desktop\Project\\Navigator\\to_save', 500)
