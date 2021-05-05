#!/usr/bin/env python3
import base64
import ctypes
import io
import json
import os
import subprocess
import time
from datetime import datetime
from collections import Counter
from pathlib import Path
from multiprocessing import Pool, Lock, Manager, Event
from matplotlib import pyplot as plt
from plot import plot_from_files, Case
from natsort import natsorted
from functools import partial


def fix_returncode(code):
    return ctypes.c_int32(code).value


class ReportGenerator:
    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")
        self.r_codes = []
        self.rvo = None
        self.nopic = None

    def generate(self, data_directory, glob='*', rvo=None, nopic=False):
        self.rvo = rvo
        self.nopic = nopic
        directories_list = []
        for path in Path(data_directory).glob(glob):
            for root, dirs, files in os.walk(path):
                if "nav-data.json" in files or 'navigation.json' in files:
                    directories_list.append(os.path.join(data_directory, root))
        directories_list = natsorted(directories_list)
        #m = Manager()
        #self.l = m.Lock()
   
        with Pool() as p:
            cases = p.map(self.run_case, directories_list)

        for case in cases:
            self.r_codes.append(fix_returncode(case["proc"].returncode))
  
        return Report(cases, self.exe, self.work_dir, self.rvo)

    def run_case(self, datadir):
        #self.e.wait()
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        if os.path.exists(Case.CASE_FILENAMES['nav_data']):
            case_filenames = Case.CASE_FILENAMES
        else:
            case_filenames = Case.CASE_FILENAMES_KT
        # Get a list of old results
        cur_path = Path('.')
        file_list = list(cur_path.glob(case_filenames['maneuvers'])) + \
                    list(cur_path.glob(case_filenames['analyse']))

        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()
        command = [self.exe, "--target-settings", case_filenames['target_settings'],
                   "--targets", case_filenames['targets_data'],
                   "--settings", case_filenames['settings'],
                   "--nav-data", case_filenames['nav_data'],
                   "--hydrometeo", case_filenames['hydrometeo'],
                   "--constraints", case_filenames['constraints'],
                   "--route", case_filenames['route'],
                   "--maneuver", case_filenames['maneuvers'],
                   "--analyse", case_filenames['analyse'],
                   "--predict", case_filenames['targets_maneuvers'],
                   ("--rvo-enable" if self.rvo is True else "")]

        completedProc = subprocess.run(command,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        print("{} .Return code: {}. Exec time: {} sec"
              .format(datadir, fix_returncode(completedProc.returncode), exec_time))
        #self.e.set()
        print("Done")
        rc = fix_returncode(completedProc.returncode)
        self.r_codes.append(rc)
        #self.e.clear()
        image_data = ""
        nav_report = ""
        if not self.nopic:
            try:
                fig = plot_from_files(os.path.join(datadir, case_filenames['nav_data']))

                f = io.BytesIO()
                fig.savefig(f, format="png", dpi=300)
                image_data = '<img width="100%" src="data:image/png;base64,{}">'.format(
                    base64.b64encode(f.getvalue()).decode())
                plt.close(fig)
            except:
                image_data = "Plot failed"
        try:
            with open("nav-report.json", "r") as f:
                nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
        except FileNotFoundError:
            pass

        os.chdir(working_dir)
        return {"datadir": datadir,
                "proc": completedProc,
                "image_data": image_data,
                "exec_time": exec_time,
                "nav_report": nav_report,
                "command": command,
                "code": fix_returncode(completedProc.returncode)}


class Report:

    def __init__(self, cases, executable, work_dir, rvo):

        self.cases = cases
        self.exe = executable
        self.work_dir = work_dir
        self.rvo = rvo

    def save_html(self, filename):
        css = """
        *{font-family: sans-serif;}
        h2 {margin-top: 2em;}
        .case {
            display: flex;
            max-height: 540pt;
            font-family: sans-serif;
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
            background: #555;
            overflow-y: auto;
        }
        .stdout pre {
            max-height: 100%;
            overflow-y: auto;
            color: #fff;
            margin: 0;
            padding: 1em;
            white-space: pre-line;
            font-family: monospace;
        }
        .stdout pre.cmd::before {
            content: '$ ';
            font-weight: bold;
        }
        .stdout pre.cmd {background: #222;}
        .stdout p{
            border-bottom: 1px black solid;
            padding: 0.5em;
            margin: 0;
            font: 400 13.3333px sans-serif;
        }
        .stdout input[type=checkbox] {
            visibility: visible;
            height: 2em;
            width: 100%;
            margin: 0;
        }
        .stdout input[type=checkbox]:after, .stdout p{
            visibility: visible;
            display: block;
            padding: 0.5em;
            background: #fff;
        }

        .stdout input[type=checkbox] + div {
            display: none;
        }
        .stdout input[type=checkbox]:checked + div {
            display: block;
        }
        .stdout input[type=checkbox]::after{content: '▸ ' attr(text);}
        .stdout input[type=checkbox]:checked::after{content: '▾ ' attr(text);}
        img{
            image-rendering: -moz-crisp-edges;         /* Firefox */
            image-rendering:   -o-crisp-edges;         /* Opera */
            image-rendering: -webkit-optimize-contrast;/* Webkit (non-standard naming) */
            image-rendering: crisp-edges;
            -ms-interpolation-mode: nearest-neighbor;
        }
        table.summary {
            border-collapse: collapse;
        }
        
        table.summary td[code="0"]{
            background-color: green;
            color: white;
        }
        table.summary td[code="1"]{
            background-color: darkorange;
            color: white;
        }
        table.summary td[code="2"]{
            background-color: red;
            color: white;
        }
        """

        tbody = ''.join([f'<tr><td>{os.path.relpath(case["datadir"], self.work_dir)}</td><td code="{case["code"]}">{case["code"]}</td></tr>' for case in
                         self.cases])
        codes = dict(Counter([case["code"] for case in self.cases]))
        table = """
        <table class="summary" border="1">
        <thead><tr><td>Case</td><td>Code</td></tr></thead>
        <tbody>{tbody}</tbody>
        <tfoot><tr><td></td><td>{code_summary}</td></tr></tfoot>
        </table>
        """.format(tbody=tbody, code_summary='<br>'.join(['{}: {}'.format(k, codes[k]) for k in sorted(codes)]))

        html = """<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Results from {datetime}</title>
<style>{styles}</style>
</head>
<body>
<h1>Report from {datetime} {rvo}</h1>""".format(datetime=datetime.now(), styles=css, rvo='<b>rvo enabled</b>' if self.rvo else '')
        html += table

        for case in self.cases:
            img_tag = case["image_data"]
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
<div><pre>{nav_report}</pre></div>
<input type="checkbox" text="STDOUT"{checked}><div>
<pre class="cmd">{command}</pre>
<pre>{stdout}</pre></div>
</div></div></div>""".format(casename=case["datadir"],
                             return_code=fix_returncode(case["proc"].returncode),
                             exec_time=case["exec_time"],
                             command=str(' '.join(case["command"])),
                             stdout=str(case["proc"].stdout.decode("utf-8")),
                             nav_report=case["nav_report"],
                             image=img_tag,
                             checked=" checked")

        html += "</body></html>"
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(html)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--glob", type=str, default='*', help="Pattern for scanned directories")
   
    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--nopic", action="store_true", help="")
    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    args = parser.parse_args()
   
    use_rvo = None
    if args.rvo:
        use_rvo = True
    
    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    t0 = time.time()
   
    #cur_dir = "/mnt/d/WORK/PROJ_KRNDT/KTViz/KTViz/bks_tests"#os.path.abspath(os.getcwd())
    #usv_executable = "/mnt/d/WORK/PROJ_KRNDT/BKS-7.2.0/out/build/WSL-GCC-Debug/src/USV"#os.path.join(cur_dir, args.executable)
    report = ReportGenerator(usv_executable)
    a = report.generate(cur_dir)
    print(report.r_codes)
    a.save_html("/mnt/d/WORK/PROJ_KRNDT/KTViz/KTViz/report75.html")
    
    import pickle

    with open("return_codes.txt", 'wb') as fp:
         pickle.dump(report.r_codes, fp)




