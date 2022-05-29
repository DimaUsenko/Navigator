from itertools import chain, combinations
import copy
import numpy as np
import pandas as pd
import xlsxwriter
import matplotlib.pyplot as plt
import os
import networkx as nx

class Nav:
    def __init__(self,path_to_matrix, path_to_capactities,path_to_request, path_to_save, allowable_radius = None):
        self.path_for_save = path_to_save

        self.allowable_radius = allowable_radius

        self.__get_start_base(path_to_request)

        self.__get_path_matrix(path_to_matrix)

        self.__get_capacities(path_to_capactities)

        self.__get_request(path_to_request)

        self.__get_all_paths()

    def __get_start_base(self,path_to_request):
        df = pd.read_excel(path_to_request)
        df = df.fillna(0)
        for v in df['База']:
            if v:
                self.start_base = str(int(v))

    def __get_request(self,path_to_request):
        df = pd.read_excel(path_to_request)
        df = df.fillna(0)

        ci = copy.copy(self.ci_dict)
        for ci_name in self.ci_dict.keys():
            ci[ci_name]=0
        for i in df['Тип СИ']:
            ci[i] += 1
        self.request= list(ci.values())

    def __get_capacities(self,path_to_capacities):
        df = pd.read_excel(path_to_capacities).fillna(0)
        
        if self.allowable_radius is not None:
            df.drop(df.index[self.__far_bases_column_index], inplace=True)
        
        self.ci_count = None

        self.ci_dict  = {ci_name: ind for ind,ci_name in enumerate(list(df.columns)[1:])} #Slice [1:] Because first column is None

        for row in df.itertuples():
            if self.ci_count is None:
                self.ci_count = len(row[2:])
            self.bases_dict[str(row[1])].append(tuple(row[2:]))

    def __get_path_matrix(self,path_to_matrix):
        df = pd.read_excel(path_to_matrix, dtype=str)
        df.columns = df.columns.map(str)

        if self.allowable_radius is not None:
            self.__far_bases_column_index = [ind-1 for ind,val in enumerate(list(df.iloc[df.columns.get_loc(self.start_base)-1])) if int(val)>self.allowable_radius]

            self.__far_bases_names = [base_name for ind,base_name in enumerate(list(df.columns)[1:]) if ind in self.__far_bases_column_index]
        
            for base_name in df.columns:
                if base_name != 'Unnamed: 0' and base_name in self.__far_bases_names:
                    df = df.drop(base_name, 1)

            df.drop(df.index[self.__far_bases_column_index], inplace=True)
        self.path_matrix = [list(row)[2:] for row in df.itertuples()]
        self.bases_dict = {base: [ind,] for ind, base in enumerate(list(df.columns[1:]))}
        
    def __powerset(self,list_name):
        s = list(list_name)
        return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
    
    def __get_path_capacity(self,path):
        path_cap = [self.bases_dict[base][1]  for base in path]
        return list(map(sum, zip(*path_cap)))
    
    def __check_cap(self,cap):
        for ind, val in enumerate(cap):
            if val>=0:
                cap[ind]=True
            else:
                cap[ind] = False
        return all(cap)

    def __path_is_permited(self,request_cap,path):
        current_cap = self.__get_path_capacity(path)
        res = np.array(current_cap) - np.array(request_cap) #TODO make tiny
        res = res.tolist()
        return self.__check_cap(res)
            

    def __get_path_len(self,path):
        #At first we need to add start base in 0 index and -1 index
        path_copy = list(copy.copy(path))
        path_copy.insert(0,self.start_base)
        path_copy.append(self.start_base)

        path_len = 0
        for i in range(len(path_copy) - 1):
            path_len += int(self.path_matrix[self.bases_dict[path_copy[i]][0]][self.bases_dict[path_copy[i+1]][0]])
        return path_len

    @staticmethod
    def k_from_val(v_search, d):
        for name, ind in d.items(): 
            if ind == v_search:
                return name

    def __write_to_excel(self):
        workbook = xlsxwriter.Workbook(self.path_for_save + '/output.xlsx')
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        worksheet.write('A1', 'Старт:' + str(self.start_base), bold)
        worksheet.write('B1', 'Длина:' + str(self.min_len), bold)
        
        row = 2
        col = 0
        req_arr = copy.copy(self.request)
        for base_name in self.min_path:
            worksheet.write(f'A{row}', 'База: ', bold)
            worksheet.write(f'B{row}', str(base_name), bold)
            base_cap = self.bases_dict[base_name][1]
            base_load = [0 for _ in range(len(base_cap))]
            for ind,value in enumerate(base_cap):
                if req_arr[ind]>0 and base_cap[ind]>0:
                    req_arr[ind] -= base_cap[ind]
                    base_load[ind] = base_cap[ind]
            to_excel = {} # Make gen
            for ind,value in enumerate(base_load):
                if value>0:
                    to_excel[self.k_from_val(ind,self.ci_dict)] = value
            for item, value in to_excel.items():
                worksheet.write(row, col, item)
                worksheet.write(row, col + 1, value)
                row += 1
            #print(base_name, to_excel)
        workbook.close()

    def __get_graph(self, draw_weights = False):

        

        arr = copy.copy(self.path_matrix)

        bases_dict_lite = {base_name: ind[0] for base_name, ind in self.bases_dict.items()}
        matrix_p = []
        for i in range(len(arr)):
            for j in range(len(arr)):
                if int(arr[i][j]) > 0:
                    c = [str(self.k_from_val(i, bases_dict_lite)), str(self.k_from_val(j, bases_dict_lite)),
                         int(arr[i][j]) / 10000]
                    matrix_p.append(c)

        G = nx.DiGraph()
        G.add_weighted_edges_from(matrix_p)
        weights = nx.get_edge_attributes(G, 'weight')
        pos = nx.circular_layout(G)
        nx.draw_networkx(G, pos=pos, node_size=1000)

        if draw_weights:
            nx.draw_networkx_edge_labels(G, pos, edge_labels=weights)
        if os.path.exists(self.path_for_save + "/Graph.png"):
            os.remove(self.path_for_save + "/Graph.png")
        plt.savefig(self.path_for_save + "/Graph.png", format="PNG")
        
        print(bases_dict_lite)
        G.clear()

        del G
        del arr
        del bases_dict_lite
        del matrix_p
        del weights
        del pos
    
    def __get_all_paths(self):

        
        if len(self.path_matrix)!=len(self.path_matrix[0]):
            print('Матрица путей не симметрична.')
            return 0
        else:
            print(f'Матрица путей размером {len(self.path_matrix)}x{len(self.path_matrix)}')

        bases_without_start = copy.copy(list(self.bases_dict.keys()))
        
        bases_without_start.remove(self.start_base)

        min_len, min_path = None, None
        
        s = bases_without_start

        self.amount_of_all_paths = 2**int(len(bases_without_start))

        x = len(s)

        for i in range(1<<x):
            curr_path  = [s[j] for j in range(x) if (i & (1<<j))]
            if curr_path:
                if self.__path_is_permited(self.request,curr_path):
                    if min_len is None and min_path is None:
                        min_len = self.__get_path_len(curr_path)
                        min_path = curr_path
                    elif self.__get_path_len(curr_path)<min_len:
                        min_len = self.__get_path_len(curr_path)
                        min_path = curr_path
                    
        if min_path is None and min_len is None and self.allowable_radius!=0:
            print(f'Для графа с указанными радиусом нет допустимых путей')

        elif min_path or min_len:
            
            print('Оптимальный путь:',min_path)
            print('Длина',min_len)

            self.min_path = min_path
            self.min_len = min_len

            self.__write_to_excel()
            self.__get_graph()
