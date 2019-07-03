import os
import shutil
import asyncio

from flask import Blueprint
from flask import request, url_for, redirect, render_template, abort, send_file
from werkzeug import secure_filename

from app import APP_ROOT
from app.filters import *
from app.tasks import Task, TaskManager

shutil.rmtree(os.path.join(APP_ROOT, "work"), True)
os.mkdir(os.path.join(APP_ROOT, "work"))

bp = Blueprint("main", __name__)
mg = TaskManager()
mg.start()

@bp.route("/", methods = ["GET"])
def home():
    tasks = mg.tasks()
    return render_template("home.j2", tasks = tasks)

def get_task(code):
    try:
        return mg.get(code)
    except KeyError:
        abort(404)
    except:
        abort(401)

@bp.route("/<int:code>", methods = ["GET"])
def view_task(code):
    task = get_task(code)
    barplot = task.barplot()
    ancestry = task.ancestry()
    return render_template("view.j2", task = task, barplot = barplot, ancestry = ancestry)

@bp.route("/<int:code>/output", methods = ["GET"])
def download_output(code):
    task = get_task(code)
    return send_file(task.outfile + "_f", "text/txt")

@bp.route("/<int:code>/log", methods = ["GET"])
def download_log(code):
    task = get_task(code)
    return send_file(task.logfile, "text/txt")

@bp.route("/<int:code>/q", methods = ["GET"])
def download_q(code):
    task = get_task(code)
    return send_file(task.qfile, "text/txt")

ALLOWED_REFERENCES = set(["", "ancestry"])
ALLOWED_EXTENSIONS = set(["csv", "tsv", "txt", "str"])

def is_file_allowed(filename):
    return (
        ("." in filename) and
        (filename.rstrip().split(".")[-1] in ALLOWED_EXTENSIONS))

def parse_form(task, error):
    ## extract values from form
    form = request.form
    task["name"] = form["name"]
    task["submitter"] = form["submitter"]
    task["reference"] = form["reference"]
    task["num_pops"] = form["num_pops"]
    task["data"] = request.files["data"]
    ## Validate values
    # submitter
    if task["submitter"] == "":
        error["submitter"] = "Missing required field"
    # reference
    if task["reference"] not in ALLOWED_REFERENCES:
        task["reference"] = ""
        error["reference"] = "Invalid reference"
    # num_pops
    try:
        task["num_pops"] = int(task["num_pops"])
        if task["num_pops"] < 1:
            error["num_pops"] = "Value must be above 1"
        if task["num_pops"] > 12:
            error["num_pops"] = "Value must be below 12"
    except:
        error["num_pops"] = "Value must be a valid number"
    # data
    if task["data"].filename == '':
        error["data"] = "Missing required field"
    if not is_file_allowed(task["data"].filename):
        error["data"] = "Invalid file extension"

@bp.route("/add", methods = ["GET", "POST"])
def add_task():
    task  = dict(name='', submitter='', reference='', num_pops=3, data=None)
    error = dict()
    if request.method == "POST":
        parse_form(task, error)
        if len(error) == 0:
            task = mg.add(**task)
            return redirect(url_for(".view_task", code = task.code))
    ## Render form
    return render_template("add.j2", task = task, error = error)