import numpy as np
import pandas as pd
#import pytest as test

import base64
import ctypes
import io
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from matplotlib import pyplot as plt
from plot import plot_from_files, Case
from natsort import natsorted

sc_type = {'None': 0,
           'Face to face': 1,
           'Overtaken': 2,
           'Overtake': 3,
           'Give way': 4,
           'Save': 5,
           'Give way priority': 6,
           'Save priority': 7,
           'Cross move': 8,
           'Cross in': 9,
           'Vision restricted forward': 10,
           'Vision restricted backward': 11}

# 0 - None
# 1 - FaceToFace
# 2 - Overtaken
# 3 - Overtake
# 4 - GiveWay
# 5 - Save
# 6 - GiveWayPriority
# 7 - SavePriority
# 8 - CrossMove
# 9 - CrossIn
# 10 - Vision restricted forward
# 11 - Vision restricted backward

# Эталонные сценарии
sc_etalon = [[4, 4, 0, 0],
             [0, 0, 0, 0],
             [1, 3, 0, 0, 0],
             [1, 0, 0, 0],
             [1, 4, 0, 4, 4],
             [0, 4, 0, 4, 0],
             [0, 0, 0, 4],
             [0, 0, 0, 4],
             [0, 0, 0, 0],
             [0, 0, 0, 0],
             [3, 3, 0, 0],
             [0, 3, 3, 0],
             [3, 3, 3, 4],
             [3, 3, 3, 0, 0],
             [3, 3, 0, 0, 3],
             [4, 3, 0, 0],
             [4, 0, 0, 0],
             [0, 4, 0, 3],
             [4, 3, 3, 0],
             [4, 3, 0, 0],
             [0, 0, 0, 0],
             [0, 0, 0, 4],
             [0, 0, 0, 0],
             [0, 3, 0, 0],
             [0, 0, 0, 0],
             [6, 3, 0, 3],
             [6, 3, 0, 3],
             [6, 6, 3, 3],
             [6, 3, 0, 0],
             [6, 0, 6, 4, 0],
             [0, 0, 0, 0],
             [0, 0, 0, 0],
             [0, 1, 0, 0],
             [0, 0, 0, 0],
             [0, 0, 0, 0],
             [6, 6, 0, 0],
             [6, 6, 6, 6],
             [6, 6, 6, 0],
             [6, 6, 6, 6, 0],
             [6, 6, 6, 6, 6],
             [6, 6, 6, 0],
             [3, 3, 0, 0],
             [0, 3, 0, 1],
             [3, 0, 3, 1],
             [0, 0, 0, 3],
             [10, 11, 10, 11],
             [10, 10, 10, 10],
             [10, 10, 10, 10],
             [11, 10, 11, 10],
             [10, 10, 11, 10, 11]]

class tester_USV:
    def __init__(self, bks_work_dir="", bks_etalon_dir=""):
        self.work = bks_work_dir
        self.etalon = bks_etalon_dir
        self.col1 = []
        self.col2 = []
        
    def tester(self, path1, path2, k):
        sc_type_local = []
        with open(path1 + "/nav-report.json", "r") as f:
            nav_report1 = json.loads(f.read())
        with open(path2 + "/nav-report.json", "r") as f:
            nav_report2 = json.loads(f.read())
        flag1 = True
        for i in range(len(nav_report1["target_statuses"])):
            if nav_report1["target_statuses"][i]["danger_level"] != nav_report2["target_statuses"][i]["danger_level"]:
                flag1 = False
                break
            else: 
                flag1 = True
        flag2 = True
        sc_t = []
        for i in range(len(nav_report1["target_statuses"])):
            sc = sc_type[nav_report1["target_statuses"][i]["scenario_type"]]
            sc_t.append(sc)
        
        for i in range(len(sc_t)):
            if sc_t[i] != sc_etalon[k][i]:
                flag2 = False

        if flag1 == True:
            self.col1.append(1)
        else:
            self.col1.append(0)
        if flag2 == True:
            self.col2.append(1)
        else:
            self.col2.append(0)
        

    #***********************************************************#    
    def scenario_runner(self):
        directories_list_work = []
        directories_list_etalon = []

        for path in Path(self.work).glob('*'):
            for root, dirs, files in os.walk(path):
                if "nav-report.json" in files:
                    directories_list_work.append(os.path.join(self.work, root))
        directories_list_work = natsorted(directories_list_work)

        for path in Path(self.etalon).glob('*'):
            for root, dirs, files in os.walk(path):
                if "nav-report.json" in files:
                    directories_list_etalon.append(os.path.join(self.etalon, root))
        directories_list_etalon = natsorted(directories_list_etalon)


        for i in range(len(directories_list_etalon)):
            self.tester(directories_list_work[i], directories_list_etalon[i], i)
        print(self.col1)
        print(self.col2)
#T = tester_USV("D:/WORK/PROJ_KRNDT/KTViz/KTViz/bks_tests/", "D:/WORK/bks_tests-master/")
#T.scenario_runner()