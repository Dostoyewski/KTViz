#!/usr/bin/env python3
import ctypes
import io
import json
import os
import time
from datetime import datetime

from matplotlib import pyplot as plt

from plot import plot_from_files


def fix_returncode(code):
    return ctypes.c_int32(code).value


class Report:

    def __init__(self, set_work_dir, maneuver_path, path_to_save_pic, interactive=False):
        # self.exe = executable
        self.man_path = maneuver_path
        self.path_picture = path_to_save_pic
        self.interactive = interactive
        self.cases = []
        self.work_dir = set_work_dir
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")

    def generate(self, data_directory, rvo=None):
        for root, dirs, files in os.walk(data_directory):
            if "nav-data.json" in files or 'navigation.json' in files:
                self.run_case(os.path.join(data_directory, root), rvo)

    def run_case(self, datadir, usv, rvo=None):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        # Get a list of old results
        # file_list = glob.glob('maneuver*.json') + glob.glob('nav-report.json')
        # for filePath in file_list:
        # try:
        # os.remove(filePath)
        # except OSError:
        # pass

        # Print the exit code.
        exec_time = time.time()
        # completedProc = subprocess.run([usv, "--targets", "target-data.json",
        # "--settings", "settings.json",
        # "--nav-data", "nav-data.json",
        # "--hydrometeo", "hmi-data.json",
        # "--constraints", "constraints.json",
        # "--route", "route-data.json",
        # "--maneuver", "maneuver.json",
        # "--analyse", "nav-report.json",
        # "--predict", "target-maneuvers.json",
        # ("--rvo" if rvo is True else "--no-rvo" if rvo is False else "")],
        # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        # print("{} .Return code: {}. Exec time: {} sec"
        # .format(datadir, fix_returncode(completedProc.returncode), exec_time))
        image_data = ""
        nav_report = ""
        # if fix_returncode(completedProc.returncode) in (0, 1):
        # if 1:
        if os.path.isfile(self.man_path):
            # fig = plot_from_files("maneuver.json", route_file="route-data.json", poly_file="constraints.json")
            # fig = plot_from_files("maneuver.json")
            fig = plot_from_files(self.man_path)
            # f = io.BytesIO()
            fig.savefig(self.path_picture)
            plt.close(fig)
            # image_data = f.getvalue().decode("utf-8")  # svg data
            # if self.interactive:
            # plugins.clear(fig)  # clear all plugins from the figure
            # plugins.connect(fig, plugins.Reset(), plugins.Zoom())
            # image_data = mpld3.fig_to_html(fig)
            # else:
            # f = io.BytesIO()
            # fig.savefig(f, format="svg")
            # image_data = f.getvalue().decode("utf-8")  # svg data

        try:
            with open("nav-report.json", "r") as f:
                nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
        except FileNotFoundError:
            pass

        os.chdir(working_dir)
        self.cases.append({"datadir": datadir,
                           # "proc": completedProc,
                           "image_data": image_data,
                           "exec_time": exec_time,
                           "nav_report": nav_report})

    def savehtml(self, filename):
        css = """
        h2 {{margin-top: 2em;}}
        .case {
            display: flex;
            max-height: 540pt;
        }
        .case .pic {
            flex: 1;
        }
        .case .stdout {
            flex: 1;
            border: 1px black solid;
            padding: 0;
            display: flex;
            flex-direction: column;
        }
        .stdout pre {
            max-height: 100%;
            overflow-y: auto;
            background: #555;
            color: #fff;
            margin: 0;
            padding: 1em;
        }
        .stdout p{
            border-bottom: 1px black solid;
            padding: 0.5em;
            margin: 0;
        }
        .stdout input[type=checkbox] {
            visibility: visible;
            height: 2em;
            width: 100%;
        }

        .stdout input[type=checkbox]:after {
            content: attr(text);
            visibility: visible;
            display: block;
            padding: 0.5em;
        }

        .stdout input[type=checkbox] + pre {
            display: none;
        }
        .stdout input[type=checkbox]:checked + pre {
            display: block;
        }
        """

        html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>results from {datetime}</title>
<style>{styles}</style>
<script type="text/javascript" src="http://d3js.org/d3.v3.min.js"></script>
</head>
<body>
<h1>report from {datetime}</h1>""".format(datetime=datetime.now(), styles=css)

        for case in self.cases:
            # if case["proc"].returncode in (0, 1):
            if 0:
                img_tag = case["image_data"]
            else:
                img_tag = ""

            html += """<div>
<h2>{casename}</h2>
<div class="case">
<div class="pic">
<picture>{image}</picture>
</div>
<div class="stdout">
<p>return code: {return_code}</p>
<p>execution time: {exec_time} seconds</p>
<input type="checkbox" text="situation report">
<pre>{nav_report}</pre>
<input type="checkbox" text="stdout"{checked}>
<pre>{stdout}</pre>
</div></div></div>""".format(casename=case["datadir"],
                             return_code=fix_returncode(1),
                             exec_time=case["exec_time"],
                             stdout=str('0'),
                             nav_report=case["nav_report"],
                             image=img_tag,
                             checked=" checked")

        html += "</body></html>"
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(html)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    # parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("set_work_dir", type=str, help="set_work_dir")
    parser.add_argument("maneuver_path", type=str, help="Path to manever file")
    parser.add_argument("path_to_save_pic", type=str, help="Path to save pic")
    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--no-rvo", action="store_true", help="Run USV with --no-rvo")
    parser.add_argument("--interactive", action="store_true", help="Make interactive plots (can be heavy)")
    args = parser.parse_args()

    use_rvo = None
    if args.rvo:
        use_rvo = True
    if args.no_rvo:
        use_rvo = False

    cur_dir = os.path.abspath(args.set_work_dir)
    # usv_executable = os.path.join(cur_dir, args.executable)
    man_path = os.path.join(args.maneuver_path)
    path_pic = os.path.join(args.path_to_save_pic)
    report = Report(cur_dir, man_path, path_pic, interactive=args.interactive)
    report.generate(cur_dir, rvo=use_rvo)
    # report.savehtml("report.html")
