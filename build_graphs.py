import datetime
import os
from math import cos, sin, radians

import matplotlib.pyplot as plt
import pandas as pd

vel_param = [4, 6.5, 8.5, 9.8, 12.2, 16, 19, 20]
vel_param_x = [4, 4.333, 4.666, 5, 6, 7, 8, 8.333]

vel_func = lambda x: 3.06 * x - 5.502

unsolved_x = [5, 6, 7, 8, 9, 10, 11, 11.5]
unsolved_y = [81, 91, 96, 100, 100, 100, 100, 100]


def get_n_targets(name):
    """
    Detects number of targets in case
    @param name: foldername with path
    @return:
    """
    foldername = os.path.split(name)[1]
    foldername2 = foldername.split(sep="_")
    if float(foldername2[1]) == 0 or float(foldername2[2]) == 0:
        return 1
    else:
        return 2


def build_percent_diag(filename, dist_max, dist_min, step):
    """
    Builds percent diagram with codes and errors to velocities graph
    @param filename:
    @param dist_max:
    @param dist_min:
    @param step:
    @return:
    """
    df = pd.read_excel(filename)
    names = df['datadir']
    codes = df['code']
    N = int((dist_max - dist_min) / step)
    dists = [dist_min + i * step for i in range(N + 1)]
    N_dists = [0 for i in range(N + 1)]
    code0 = [0 for i in range(N + 1)]
    code1 = [0 for i in range(N + 1)]
    code2 = [0 for i in range(N + 1)]
    code4 = [0 for i in range(N + 1)]
    code5 = [0 for i in range(N + 1)]
    code4_fnmes = []
    vel2 = []
    dist2 = []
    f_names2 = []
    for i, name in enumerate(names):
        foldername = os.path.split(name)[1]
        n_targ = get_n_targets(foldername)
        foldername2 = foldername.split(sep="_")
        dist = 0
        if n_targ == 1:
            dist = max(float(foldername2[1]), float(foldername2[2]))
        elif n_targ == 2:
            dist = min(float(foldername2[1]), float(foldername2[2]))
        if codes[i] == 0:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code0[ind] += 1
                N_dists[ind] += 1
        elif codes[i] == 2:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code2[ind] += 1
                N_dists[ind] += 1
            vel2.append(float(foldername2[3]))
            dist2.append(dist)
            if float(foldername2[3]) < vel_func(dist):
                f_names2.append(foldername)
        elif codes[i] == 4:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code4[ind] += 1
                N_dists[ind] += 1
            code4_fnmes.append(foldername)
        elif codes[i] == 1:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code1[ind] += 1
                N_dists[ind] += 1
        elif codes[i] == 5:
            ind = round((dist - dist_min) / step)
            if N_dists[ind] > -1:
                code5[ind] += 1
                N_dists[ind] += 1
    fig, ax = plt.subplots()
    for i in range(N + 1):
        if N_dists[i] == 0:
            N_dists[i] = 1
    df4 = pd.DataFrame()
    df4['names_4'] = code4_fnmes
    df4.to_excel("4code_tests.xlsx")
    plt.figure(figsize=(10, 6), dpi=200)
    ddf = pd.DataFrame()
    ddf['critical'] = f_names2
    ddf.to_excel("critical.xlsx")
    code0_p = [code0[i] / N_dists[i] * 100 for i in range(N + 1)]
    code1_p = [code1[i] / N_dists[i] * 100 for i in range(N + 1)]
    code2_p = [code2[i] / N_dists[i] * 100 for i in range(N + 1)]
    code4_p = [code4[i] / N_dists[i] * 100 for i in range(N + 1)]
    code5_p = [code5[i] / N_dists[i] * 100 for i in range(N + 1)]
    print(N_dists)
    plt.plot(dists, code0_p, 'b', label="Код 0", linewidth=3)
    print(code0_p)
    # plt.fill_between(dists, code0_p, 100, color='orange', alpha=0.5)
    # plt.fill_between(dists, code0_p, 0, color='green', alpha=0.5)
    plt.plot(dists, code1_p, 'r', label="Код 1")
    plt.plot(dists, code2_p, 'y--', label="Код 2")
    plt.plot(dists, code4_p, 'o--', label="Код 4")
    plt.plot(dists, code5_p, 'g', label="Код 5")
    plt.grid()
    plt.axis([dist_min, dist_max, 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=20)
    plt.ylabel('Маневр построен, %', fontsize=20)
    # plt.plot(unsolved_x, unsolved_y, 'o--')
    plt.legend(loc='upper left', shadow=True)
    plt.title("Дата: " + str(datetime.date.today()) + ", цели: " + str(n_targ))
    plt.savefig("./images/" + str(datetime.date.today()) + "_" + str(n_targ) + "_stats.png")
    plt.show()
    fig, ax = plt.subplots()
    plt.scatter(dist2, vel2, alpha=0.5)
    plt.plot(vel_param_x, vel_param)
    plt.xlabel('Дистанция до цели, мили')
    plt.ylabel('Скорость цели, узлы')
    plt.grid()
    plt.title("Дата: " + str(datetime.date.today()) + ", цели: " + str(n_targ))
    plt.savefig("./images/" + str(datetime.date.today()) + "_" + str(n_targ) + "_vels.png")
    plt.show()


def build_turn_diagram(filename, dist_max, dist_min, step):
    df = pd.read_excel(filename)
    names = df['datadir']
    turns = df['right']
    N = int((dist_max - dist_min) / step)
    dists = [dist_min + i * step for i in range(N + 1)]
    N_dists = [0 for i in range(N + 1)]
    left = [0 for i in range(N + 1)]
    right = [0 for i in range(N + 1)]
    left_names = []

    for i, name in enumerate(names):
        foldername = os.path.split(name)[1]
        n_targ = get_n_targets(foldername)
        foldername2 = foldername.split(sep="_")
        dist = 0
        if n_targ == 1:
            dist = max(float(foldername2[1]), float(foldername2[2]))
        elif n_targ == 2:
            dist = min(float(foldername2[1]), float(foldername2[2]))
        ind = round((dist - dist_min) / step)
        if turns[i] == True:
            right[ind] += 1
            N_dists[ind] += 1
        elif turns[i] == False:
            left[ind] += 1
            N_dists[ind] += 1
            left_names.append(foldername)
    df = pd.DataFrame()
    df['dirnames'] = left_names
    df.to_excel('./reports/' + str(n_targ) + '_left_maneuvers.xlsx')
    fig, ax = plt.subplots()
    for i in range(N + 1):
        if N_dists[i] == 0:
            N_dists[i] = 1
    plt.figure(figsize=(10, 6), dpi=200)
    right_p = [right[i] / N_dists[i] * 100 for i in range(N + 1)]
    left_p = [left[i] / N_dists[i] * 100 for i in range(N + 1)]

    plt.plot(dists, right_p, 'b', label="Поворот вправо", linewidth=3)
    plt.plot(dists, left_p, 'r', label="Поворот влево", linewidth=3)

    plt.grid()
    plt.axis([dist_min, dist_max, 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=20)
    plt.ylabel('Поворот в сторону, %', fontsize=20)

    plt.legend(loc='upper left', shadow=True)
    plt.title("Дата: " + str(datetime.date.today()) + ", цели: " + str(n_targ))
    plt.savefig("./images/" + str(datetime.date.today()) + "_" + str(n_targ) + "_turns.png")
    plt.show()


if __name__ == "__main__":
    build_percent_diag('./reports/report1_2021-07-20.xlsx', 12, 4, 0.5)
    build_turn_diagram('./reports/report1_2021-07-20.xlsx', 12, 4, 0.5)
    build_percent_diag('./reports/report2_2021-07-20.xlsx', 12, 4, 0.5)
    build_turn_diagram('./reports/report2_2021-07-20.xlsx', 12, 4, 0.5)
    df = pd.read_excel('./reports/report_2_4.xlsx')
    names = df['datadir']
    x1, y1, c1 = [], [], []
    x2, y2, c2 = [], [], []
    fig, ax = plt.subplots()
    # скорость судна скорость цели
    # тесты для одной цели
    for name in names:
        foldername = name.split(sep="\\")[6]
        foldername = foldername.split(sep="_")
        x1.append(cos(radians(float(foldername[3]))) * float(foldername[1]))
        x2.append(cos(radians(float(foldername[4]))) * float(foldername[2]))
        y1.append(sin(radians(float(foldername[3]))) * float(foldername[1]))
        y2.append(sin(radians(float(foldername[4]))) * float(foldername[2]))
        c1.append("#17becf")
        c2.append('#d62728')
    plt.scatter(x1, y1, c=c1, alpha=0.5, label="Цели №1")
    plt.scatter(x2, y2, c=c2, alpha=0.5, label="Цели №2")
    plt.plot(0, 0, 'y*', linewidth=2, markersize=12, label="Наше судно")
    plt.grid()
    legend = ax.legend(loc='upper left', shadow=True, fontsize='x-large')
    plt.show()
