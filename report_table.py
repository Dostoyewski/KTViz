import numpy as np
import pandas as pd

  
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

    def save_file(self, name):
        with pd.ExcelWriter(name) as writer:
              self.table.to_excel(writer)

