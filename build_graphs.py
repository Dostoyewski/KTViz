from math import cos, sin, radians

import matplotlib.pyplot as plt
import pandas as pd

if __name__ == "__main__":
    df = pd.read_excel('report_2_4_old.xlsx')
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
