import os
import datetime
import asyncio
import queue
import subprocess
import signal

from enum import Enum
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

from app import APP_ROOT
from app.names import get_name

FIXMID = dict(MID675="MID675", MDI1391="MID1391", MDI1785="MID1785", MID1636="MID1632")

def fix_mid(name):
    if name in FIXMID:
        return FIXMID[name]
    return name

def write_str(filename, data):
    with open(filename, "w") as fs:
        variants = data["variants"]
        
        fs.write(" " + " ".join(variants) + "\n") # print header
        for name in data["data"]:
            # Sanitize name for printting
            l0 = [name.replace(" ", "_")]
            l1 = [name.replace(" ", "_")]
            for v in variants:
                if v not in data["data"][name]:
                    l0.append("-9")
                    l1.append("-9")
                    continue
                l0.append(data["data"][name][v][0])
                l1.append(data["data"][name][v][1])
            fs.write(" ".join(l0) + "\n")
            fs.write(" ".join(l1) + "\n")


def parse_data(filename, result = None):
    extension = filename.split(".")[-1]
    if extension == "csv":
        return parse_delim(filename, result, delim = ",")
    elif extension == "str":
        return parse_str(filename, result)
    else:
        return parse_delim(filename, result, delim="\t")

def write_q(filename, data):
    fs = open(filename, "w")
    for name in data["names"]:
        contribution = ["%0.3f" % v for v in data[name]]
        fs.write("\t".join([name] + contribution) + "\n")

def parse_q(filename):
    data = dict(names = [])
    fs = open(filename)
    ## Skip until contribution table
    while not next(fs).startswith("Inferred ancestry"):
        pass
    ## Skip header
    next(fs)
    ## Extract values
    line = next(fs)
    while line != "":
        fields = line.rstrip().split()
        if len(fields) == 0:
            break
        name = fields[1]
        contribution = fields[4:]
        data["names"].append(name)
        data[name] = [float(v) for v in contribution]
        # Move cursor
        line = next(fs)
    return data

def parse_delim(filename, result = None, delim = None):
    if result is None:
        result = dict(variants = set([]), data = dict())
    with open(filename) as fs:
        header = next(fs).rstrip().split(delim)[1:]
        header = [fix_mid(name) for name in header]
        result["variants"] = result["variants"].union(header)
        for line in fs:
            name, *fields = line.split(delim)
            name = name.replace(" ", "_")
            result["data"][name] = dict()
            for i in range(len(header)):
                fields[i] = fields[i].rstrip()
                if fields[i] == "":
                    gt = ["-9", "-9"]
                else:
                    gt = [fields[i][0], fields[i][1]]
                result["data"][name][header[i]] = gt
    return result


def parse_str(filename, result = None):
    if result is None:
        result = dict(variants = set([]), data = dict())
    with open(filename) as fs:
        header = next(fs).rstrip().split()[1:]
        header = [fix_mid(name) for name in header]
        result["variants"] = result["variants"].union(header)
        while True:
            a = next(fs, None)
            b = next(fs, None)
            if a is None or b is None:
                break
            name, *a = a.rstrip().split()
            b = b.rstrip().split()[1:]
            name = name.replace(" ", "_")
            result["data"][name] = dict()
            for i in range(len(header)):
                result["data"][name][header[i]] = [a[i], b[i]]
    return result

REFERENCE = dict(
    ancestry = parse_str(os.path.join(APP_ROOT, "resource", "ancestry.str"))
)
REFERENCE_LABEL = dict(
    ancestry = dict(label = ["European", "Nat. American", "African"], size = [290, 246, 200])
)

class Task(object):
    class Status (Enum):
        Queued   = 0
        Running  = 1
        Complete = 2
        Failure  = 3
        Canceled = 4

    def __init__(self, code, name, submitter, num_pops, reference, data, **kwargs):
        if name == "" or name is None:
            name = get_name()
        now = datetime.datetime.now()
        self.code = code
        self.name = name
        self.submitter = submitter
        self.num_pops = num_pops
        self.reference = reference
        self.created_at = now
        self.updated_at = now
        self.status = self.Status.Queued
        # private
        self._workdir = os.path.join(APP_ROOT, "work", "task%03d" % self.code)
        self._file = os.path.join(self._workdir, secure_filename(data.filename))
        os.mkdir(self._workdir)
        data.save(self._file)

    def __str__(self):
        return "Task #%d : %s" % (self.code, self.name)
    
    def barplot(self):
        if self.status != Task.Status.Complete:
            return []
        names = self.q["names"]
        barplot = [
            dict(x = [], y = [], name = "Pop #%03d" % i, type = "bar")
            for i in range(self.num_pops)
        ]
        to_skip = 0
        if self.reference in REFERENCE_LABEL:
            ref = REFERENCE_LABEL[self.reference]
            for i in range(len(ref["label"])):
                acc = [0 for _ in range(self.num_pops)]
                for j in range(ref["size"][i]):
                    for z in range(self.num_pops):
                        acc[z] += self.q[names[j + to_skip]][z]
                acc_total = sum(acc)
                acc = [v/acc_total for v in acc]
                for j in range(self.num_pops):
                   barplot[j]["x"].append(ref["label"][i])
                   barplot[j]["y"].append(acc[j])
                to_skip += ref["size"][i]
        for i in range(to_skip, len(names)):
            for j in range(self.num_pops):
                barplot[j]["x"].append(names[i])
                barplot[j]["y"].append(self.q[names[i]][j])
        return barplot

    def ancestry(self):
        if self.status != Task.Status.Complete:
            return dict(names = [])
        if self.reference not in REFERENCE_LABEL:
            return self.q
        ref = REFERENCE_LABEL[self.reference]
        to_skip = sum(ref["size"])
        names = self.q["names"][to_skip:]
        res = dict(names = names)
        for name in names:
            res[name] = self.q[name]
        return res


    def execute(self):
        self.status = self.Status.Running
        # Prepare data
        data = parse_data(self._file, REFERENCE.get(self.reference))
        # Parameters
        mnpar = os.path.join(APP_ROOT, "resource", "mainparams")
        expar = os.path.join(APP_ROOT, "resource", "extraparams")
        npop = self.num_pops
        nind = len(data["data"])
        nloc = len(data["variants"])
        iptf = os.path.join(self._workdir, "infile")
        outf = os.path.join(self._workdir, "outfile")
        logf = os.path.join(self._workdir, "logfile")
        cmdf = os.path.join(APP_ROOT, "resource", "structure_src", "structure")
        write_str(iptf, data)
        # Run command
        cmd = [
            cmdf, "-m", mnpar, "-e", expar,
            "-K", str(npop), "-L", str(nloc), "-N", str(nind),
            "-i", iptf, "-o", outf
        ]
        print(" ".join(cmd))
        proc = subprocess.run(cmd, stdout = open(logf, "w"))
        if proc.returncode != 0:
            self.status = self.Status.Failure
        else:
            print("processing output")
            self.q = parse_q(outf + "_f")
            print("processing output2")
            write_q(os.path.join(self._workdir, "ancestry.tsv"), self.q)
            self.status = self.Status.Complete

    def run(self):
        self.updated_at = datetime.datetime.now()
        self.status = self.Status.Running
    
    def complete(self):
        self.updated_at = datetime.datetime.now()
        self.status = self.Status.Complete

    def fail(self):
        self.updated_at = datetime.datetime.now()
        self.status = self.Status.Failure

    def cancel(self):
        self.updated_at = datetime.datetime.now()
        self.status = self.Status.Canceled

class ServiceExit(Exception):
    pass

def shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit


class TaskManager(object):
    def __init__(self):
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        self._at = 0
        self._collection = dict()
        self._queue = queue.Queue()
        self._workers = ThreadPoolExecutor(8)

    def _worker(self):
        while self._is_running:
            try:
                code = self._queue.get(timeout=5)
                task = self.get(code)
                task.execute()
                self._queue.task_done()
            except queue.Empty:
                continue
        
    def stop(self):
        self._is_running = False
        self._workers.shutdown()
        raise KeyboardInterrupt

    def start(self):
        stop_handler = lambda signum, frame: self.stop()
        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)

        self._is_running = True
        for i in range(8):
            self._workers.submit(self._worker)

    def add(self, name, submitter, num_pops, reference, data, **kwargs):
        task = Task(self._at, name, submitter, num_pops, reference, data)
        self._collection[self._at] = task
        self._queue.put(self._at)
        self._at += 1
        return task

    def get(self, code):
        return self._collection[code]

    def has(self, code):
        return code in self._collection
    
    def tasks(self):
        self._clear()
        tasks = list()
        for key in self._collection:
            tasks.append(self._collection[key])
        tasks.sort(key = lambda t: t.updated_at)
        return tasks

    def _clear(self):
        now = datetime.datetime.now()
        to_remove = list()
        for key in self._collection:
            task = self._collection[key]
            if (task.updated_at - now) > datetime.timedelta(days = 7):
                to_remove.append(k)
        for key in to_remove:
            del self._collection[key]