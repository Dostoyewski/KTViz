import numpy as np
import pandas as pd
#from StyleFrame import StyleFrame, Styler
import tester_USV
#col1= [1, 0, 1, 0, 1]
#col2 = [1, 1, 1, 1, 1]
#col3 = [1, 2, 0, 1, 2]
#names_rows = ['1-1', '1-2', '1-3', '1-4', '1-5']
n_r =      ['1-1', '1-2', '1-3', '1-4', '1-5',
                  '2-1', '2-2', '2-3', '2-4', '2-5',
                  '3-1', '3-2', '3-3', '3-4', '3-5',
                  '4-1', '4-2', '4-3', '4-4', '4-5',
                  '5-1', '5-2', '5-3', '5-4', '5-5',
                  '6-1', '6-2', '6-3', '6-4', '6-5',
                  '7-1', '7-2', '7-3', '7-4', '7-5',
                  '8-1', '8-2', '8-3', '8-4', '8-5',
                  '9-1', '9-2', '9-3', '9-4', '9-5',
                  '10-1', '10-2', '10-3', '10-4', '10-5']
  
class excel_report:
    def __init__(self, names_rows, col1, col2, col3):
        self.names = names_rows
        self.c1 = col1
        self.c2 = col2
        self.c3 = col3
        self.table = pd.DataFrame(columns=["Scenario Name", "Ranging Dangerous", "Detect Situation", "Return Code"])
    
    def color_mapping(self, val):
        if val == 0:
            color = 'red'
        else:
            color = 'green'
        return 'background-color: %s' % color
   
    def build_table(self):
        for i in range(len(self.c1)):
            self.table.loc[len(self.table)] = [self.names[i], self.c1[i], self.c2[i], self.c3[i]]

    def save_file(self):
        with pd.ExcelWriter('report.xlsx') as writer:
              self.table.to_excel(writer)
 
# Интсрукция
# Снача запускается bks-report.py 
# Затем запускается этот файл. На выходе он выдает таблицу в excel

# В эта часть получает первые три столбца таблицы
# В качестве первого указывается путь к файлам bks_tests, полученным в результате работы текущей версии программы
# Второй путь к файлам с репозитория https://github.com/mangoozt/bks_tests.git , которые сохранены на Вашем компьютере
T = tester_USV.tester_USV("D:/WORK/PROJ_KRNDT/KTViz/KTViz/bks_tests/", "D:/WORK/bks_tests-master/")
T.scenario_runner()  
import pickle
with open("return_codes.txt", 'rb') as f:
    rc = pickle.load(f)
# Эта часть кода делает из четырех списков pandas DataFrame и сохраняет его в файл excel. Этот файл будет находится в корне KTViz 
a = excel_report(n_r, T.col1, T.col2, rc)
a.build_table()
a.save_file()
print(a.table)
