#!/usr/bin/env python3
import ctypes
import io
from datetime import datetime
import time
import os
import glob
import subprocess
import sys
from main import prepare_file
import matplotlib.pyplot as plt
import json


def fix_returncode(code):
    return ctypes.c_int32(code).value


class Report:

    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")

    def generate(self, data_directory, rvo=None):
        for root, dirs, files in os.walk(data_directory):
            if "nav-data.json" in files:
                self.run_case(os.path.join(data_directory, root), executable, rvo)

    def run_case(self, datadir, usv, rvo=None):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        # Get a list of old results
        file_list = glob.glob('maneuver*.json') + glob.glob('nav-report.json')
        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()
        completedProc = subprocess.run([usv, "--targets", "target-data.json",
                                        "--settings", "settings.json",
                                        "--nav-data", "nav-data.json",
                                        "--hydrometeo", "hmi-data.json",
                                        "--constraints", "constraints.json",
                                        "--route", "route-data.json",
                                        "--maneuver", "maneuver.json",
                                        "--analyse", "nav-report.json",
                                        ("--rvo" if rvo is True else "--no-rvo" if rvo is False else "")],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        print("{} .Return code: {}. Exec time: {} sec"
              .format(datadir, fix_returncode(completedProc.returncode), exec_time))
        image_data = ""
        nav_report = ""
        if completedProc.returncode == 0:
            if os.path.isfile("maneuver.json"):
                fig, ax = plt.subplots(figsize=(10, 7.5))
                ax.clear()
                prepare_file("maneuver.json",
                             show=False,
                             ax=ax,
                             rel=False,
                             tper=0,
                             radius=1.5,
                             text=True,
                             show_dist=True,
                             is_loaded=False)
                ax.axis('equal')
                plt.draw()
                f = io.BytesIO()
                plt.savefig(f, format="svg")
                image_data = f.getvalue().decode("utf-8")  # svg data

            with open("nav-report.json", "r") as f:
                nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)

        os.chdir(working_dir)
        self.cases.append({"datadir": datadir,
                           "proc": completedProc,
                           "image_data": image_data,
                           "exec_time": exec_time,
                           "nav_report": nav_report})

    def saveHTML(self, filename):
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

        html = """<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Results from {datetime}</title>
<style>{styles}</style>
</head>
<body>
<h1>Report from {datetime}</h1>""".format(datetime=datetime.now(), styles=css)

        for case in self.cases:
            if case["proc"].returncode == 0:
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
<p>Return code: {return_code}</p>
<p>Execution time: {exec_time} seconds</p>
<input type="checkbox" text="Situation report">
<pre>{nav_report}</pre>
<input type="checkbox" text="STDOUT"{checked}>
<pre>{stdout}</pre>
</div></div></div>""".format(casename=case["datadir"],
                             return_code=fix_returncode(case["proc"].returncode),
                             exec_time=case["exec_time"],
                             stdout=str(case["proc"].stdout.decode("utf-8")),
                             nav_report=case["nav_report"],
                             image=img_tag,
                             checked=" checked" if case["proc"].returncode == 0 else "")

        html += "</body></html>"
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(html)


if __name__ == "__main__":
    executable = sys.argv[1]
    rvo = None
    if '--rvo' in sys.argv:
        rvo = True
    if '--no-rvo' in sys.argv:
        rvo = False
    cur_dir = os.path.abspath(os.getcwd())
    executable = os.path.join(cur_dir, executable)
    report = Report(executable)
    report.generate(cur_dir, rvo=rvo)
    report.saveHTML("report.html")
    # traverse root directory, and list directories as dirs and files as files
