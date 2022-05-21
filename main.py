from itertools import chain, combinations
import copy
import pandas as pd
import xlsxwriter
#from PyQt5 import QtWidgets
#from PyQt5.QtGui import QPixmap


class Base:
    def __init__(self,name,capacity,ci_col):
        self.name = name
        self.max_capacity = capacity

        self.current_mean = [0 for _ in range(ci_col)]

    def update_value(self,ind,value):
        """
        Функция вернет значение, которое "отдано"
        Если значение 0, то разгрузить уже невозможно
        """
        #
        empty = self.max_capacity[ind]-self.current_mean[ind]

        if value<=empty:
            self.current_mean[ind]+=value
            return value

        elif value>=empty and empty>=1: #ToDo проверить
            self.current_mean[ind]+=empty
            return empty
        else:
            return 0

class Navigator:
    def __init__(self,request_path,path_to_capactity,path_to_roads) -> None:
        
        
        self.load_roads(path_to_roads)

        self.load_capacities(path_to_capactity)       

        

        self.load_request(request_path)

        print(f'Запрос из {self.start_base}:')
        print(dict(zip(self.ci.keys(),self.requset)))
    
        self.get_all_paths(self.start_base)

        print('All pathes',len(self.all_paths))

        self.ch_paths()

        print('All check pathes',len(self.checked_paths))

        for path in self.checked_paths:
            path.insert(0,self.start_base)
            path.append(self.start_base)
       
        self.get_fastest_path()
        

    def load_roads(self, path_to_roads):
        df = pd.read_excel(path_to_roads)
        df = df.fillna(0)
        out = []
        self.bases_ok = []
        for row in df.itertuples():
            #print(row)
            line = []
            if int(row[2])<=500:
                
                self.bases_ok.append(row[1])
            else:
                df = df.drop(row[0], 0)
            #for i in range(2,len(row)):
            #    line.append(row[i])
            #out.append(line)
        for c_name in df.columns:
            if c_name!='Unnamed: 0' and c_name not in self.bases_ok:
                df = df.drop(c_name, 1)
        for row in df.itertuples():
            #print(row)
            line = []
            for i in range(2,len(row)):
                line.append(int(row[i]))
            out.append(line)
        #for i in out:
        #    print(i)
        print(df)
        #Проверка того, что матрица квадратная
        m = len(out)
        for line in out:
            if len(line)!=m:
                raise ValueError

        #Создание graph_ind
        
        self.graph_ind = {}
        ind = 0
        for base in df.columns.values.tolist()[1:]:
            self.graph_ind[str(base)] = int(ind)
            ind+=1
        
        print('Кол-во всевозможных Баз исходя из roads',len(out))

        self.len_matrix = out

    def load_capacities(self, path_to_capactity):
        df = pd.read_excel(path_to_capactity)
        df = df.fillna(0)
        out = []
        bases_count = 0
        #image.png
        for row in df.itertuples():
            if row[1] not in self.bases_ok:
                df = df.drop(row[0], 0)
        print(df)
        for row in df.itertuples():
            line = []
            for i in range(2,len(row)):
                line.append(row[i])
            out.append(line)
            bases_count +=1
        print('Кол-во всевозможных Си исходя из capactiy',len(row)-2)#Т.к в pd 0-ый элемент - индекс, 1-ый элемент - имя базы
        self.ci_col = len(row)-2
        print('Кол-во всевозможных Баз исходя из capactiy',bases_count)

        self.ci = {}
        for ci_ in df.columns.values.tolist()[1:]:
            self.ci[ci_] = 0
        
        for line in out:
            print(line)
        self.bases_capacity = out

    def load_request(self,path_to_request):
        df = pd.read_excel(path_to_request)
        df = df.fillna(0)

        for i in df['Тип СИ']:
            self.ci[i]+=1
        for v in df['База']:
            if v:
                self.start_base = str(int(v))
        
        self.requset = list(self.ci.values())

    def _powerset(self,list_name):
        s = list(list_name)
        return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


    def get_all_paths(self,base):
        full_list = list(self.graph_ind.keys())
        start_point = int(self.graph_ind[str(base)])
        full_list.pop(start_point)
        paths = self._powerset(full_list)
        outputs = []
        for path in paths:
            path = list(path)
            path.insert(0,base)
            path.append(base)
            outputs.append(path)

        self.all_paths = outputs        

    def ch_paths(self):
        cheched_paths = []
        
        for path_ind,path in enumerate(self.all_paths):
            request = copy.copy(self.requset)
            path.pop(0)
            path.pop(-1)
            bases = [Base(list(self.graph_ind.keys())[i],self.bases_capacity[i],self.ci_col) for i in range(len(self.len_matrix))]
            for base in path:
                base_ind = self.graph_ind[base]
                curr_base = bases[base_ind]
                for ind,value in enumerate(request):
                    request[ind]-= curr_base.update_value(ind,value)

            flag = True
            for v in request:
                if v!=0:
                    flag = False
            if flag:
                cheched_paths.append(path)

        self.checked_paths = cheched_paths

    def get_path_len(self,path):
        path_len = 0
        for i in range(len(path)-1):

            path_len+=self.len_matrix[self.graph_ind[str(path[i])]][self.graph_ind[str(path[i+1])]]

        return path_len

    def get_fastest_path(self):

        paths_lenghts = []
        for i in range(len(self.checked_paths)):
            paths_lenghts.append(self.get_path_len(self.checked_paths[i]))
        
        workbook = xlsxwriter.Workbook('output.xlsx')
        worksheet = workbook.add_worksheet()
        
        print('Самый короткий путь: ',min(paths_lenghts), self.checked_paths[paths_lenghts.index(min(paths_lenghts))])
        worksheet.write('A1', 'Старт:'+str(self.start_base))
        worksheet.write('B1', 'Длина:'+str(min(paths_lenghts)))
        curr_line = 2
        path =  self.checked_paths[paths_lenghts.index(min(paths_lenghts))]
        request = copy.copy(self.requset)
        path.pop(0)
        path.pop(-1)
        bases = [Base(list(self.graph_ind.keys())[i],self.bases_capacity[i],self.ci_col) for i in range(len(self.len_matrix))]
        for base in path:
            base_ind = self.graph_ind[base]
            curr_base = bases[base_ind]
            for ind,value in enumerate(request):
                request[ind]-= curr_base.update_value(ind,value)
        #print('----------')
        for base in bases:
            
            if any(base.current_mean):
                worksheet.write(f'A{curr_line}',str(base.name))
                worksheet.write(f'B{curr_line}',f'Отгруженное количество Cи: {base.current_mean}')
                curr_line+=1
                #print(base.name, base.current_mean)
            
        workbook.close()
#p1 = Navigator('temp/request1.xlsx','temp/capacity.xlsx','temp/roads.xlsx')
p2 = Navigator('temp2/Zayavka.xlsx','temp2/Vozmozhnosti.xlsx','temp2/Matritsa_rasstoyanii_774.xlsx')
#print(len(p1.all_paths))


#class MainApp(QtWidgets.QMainWindow, window.Ui_MainWindow):
#    def __init__(self):
#        super().__init__()
#def main():
#
#    app = QtWidgets.QApplication(sys.argv)
#    window = MainApp()
#    window.show()
#    app.exec_()
#
#
#if __name__ == '__main__':
#    main()