#!/usr/bin/env python3
import os

from matplotlib import pyplot as plt
from plot import plot_from_files

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("set_work_dir", type=str, help="set_work_dir")
    parser.add_argument("maneuver_path", type=str, help="Path to manever file")
    parser.add_argument("path_to_save_pic", type=str, help="Path to save pic")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.set_work_dir)
    man_path = os.path.abspath(args.maneuver_path)
    path_pic = os.path.abspath(args.path_to_save_pic)

    working_dir = os.path.abspath(os.getcwd())
    os.chdir(data_dir)
    if os.path.isfile(man_path):
        # fig = plot_from_files("maneuver.json", route_file="route-data.json", poly_file="constraints.json")
        # fig = plot_from_files("maneuver.json")
        fig = plot_from_files(man_path)
        fig.savefig(path_pic)
        plt.close(fig)
    os.chdir(working_dir)
