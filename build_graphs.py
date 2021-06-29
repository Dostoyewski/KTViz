from math import cos, sin, radians

import matplotlib.pyplot as plt
import pandas as pd

vel_param = [4, 6.5, 8.5, 9.8, 12.2, 16, 19, 20]
vel_param_x = [4, 4.333, 4.666, 5, 6, 7, 8, 8.333]

vel_func = lambda x: 3.06 * x - 5.502

def build_percent_diag(filename, dist_max, dist_min, step):
    df = pd.read_excel(filename)
    names = df['datadir']
    codes = df['code']
    all_tests = len(names)
    N = int((dist_max - dist_min) / step)
    dists = [dist_min + i * step for i in range(N + 1)]
    N_dists = [0 for i in range(N + 1)]
    code0 = [0 for i in range(N + 1)]
    code1 = [0 for i in range(N + 1)]
    code2 = [0 for i in range(N + 1)]
    code4 = [0 for i in range(N + 1)]
    code5 = [0 for i in range(N + 1)]
    vel2 = []
    dist2 = []
    f_names2 = []
    for i, name in enumerate(names):
        foldername = name.split(sep="\\")[6]
        foldername2 = foldername.split(sep="_")
        dist = max(float(foldername2[1]), float(foldername2[2]))
        if codes[i] == 0 or codes[i] == 5 or codes[i] == 1:
            code0[round((dist - dist_min) / step)] += 1
            N_dists[round((dist - dist_min) / step)] += 1
        # elif codes[i] == 1:
        #     code1[int((dist - dist_min) / step)] += 1
        #     N_dists[int((dist - dist_min) / step)] += 1
        elif codes[i] == 2:
            code2[round((dist - dist_min) / step)] += 1
            N_dists[round((dist - dist_min) / step)] += 1
            vel2.append(float(foldername2[3]))
            dist2.append(dist)
            if float(foldername2[3]) < vel_func(dist):
                f_names2.append(foldername)
        elif codes[i] == 4:
            code4[round((dist - dist_min) / step)] += 1
            N_dists[round((dist - dist_min) / step)] += 1
        # elif codes[i] == 5:
        #     code5[int((dist - dist_min) / step)] += 1
        #     N_dists[int((dist - dist_min) / step)] += 1
    fig, ax = plt.subplots()
    for i in range(N + 1):
        if N_dists[i] == 0:
            N_dists[i] = 1
    plt.figure(figsize=(10, 6), dpi=200)
    ddf = pd.DataFrame()
    ddf['critical'] = f_names2
    ddf.to_excel("critical.xlsx")
    code0_p = [code0[i] / N_dists[i] * 100 for i in range(N + 1)]
    code1_p = [code1[i] / N_dists[i] * 100 for i in range(N + 1)]
    code2_p = [code2[i] / N_dists[i] * 100 for i in range(N + 1)]
    code4_p = [code4[i] / N_dists[i] * 100 for i in range(N + 1)]
    code5_p = [code5[i] / N_dists[i] * 100 for i in range(N + 1)]
    plt.plot(dists, code0_p, 'b', label="Код 0", linewidth=3)
    plt.plot(dists, code1_p, 'r', label="Код 1")
    plt.plot(dists, code2_p, 'y--', label="Код 2")
    plt.plot(dists, code4_p, 'o--', label="Код 4")
    plt.plot(dists, code5_p, 'g', label="Код 5")
    plt.grid()
    plt.axis([5, dist_max, 0, 100])
    plt.xlabel('Дистанция до ближайшей цели, мили', fontsize=20)
    plt.ylabel('Маневр построен, %', fontsize=20)
    plt.legend(loc='upper left', shadow=True)
    plt.show()
    fig, ax = plt.subplots()
    plt.scatter(dist2, vel2, alpha=0.5)
    plt.plot(vel_param_x, vel_param)
    plt.xlabel('Дистанция до цели, мили')
    plt.ylabel('Скорость цели, узлы')
    plt.grid()
    plt.show()


if __name__ == "__main__":
    build_percent_diag('report.xlsx', 11, 4.5, 0.5)
    df = pd.read_excel('report_2_4.xlsx')
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
