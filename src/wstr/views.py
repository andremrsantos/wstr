import datetime

from flask import Blueprint
from flask import request, url_for, redirect, render_template, abort, send_file
from .db import db, submit_job, Job
from .name import generate_name

ALLOWED_REF_PANEL = ["", "ancestry"]
ALLOWED_EXTENSIONS = {"csv", "tsv", "txt", "str"}

base = Blueprint("main", __name__)


# General task finder
@base.before_request
def _db_connect():
    db.connect(True)


@base.teardown_request
def _db_disconnect(exc):
    if not db.is_closed():
        db.close()


def list_tasks():
    last_week = datetime.datetime.today() - datetime.timedelta(days=7)
    return Job.select()\
        .where(Job.created_at > last_week)\
        .order_by(Job.updated_at.desc())


def find_task(id):
    task = Job.get_or_none(id=id)
    if task is None:
        return abort(404)
    return task


# Build task creation form
def is_file_allowed(filename):
    return (
        ("." in filename) and
        (filename.rstrip().split(".")[-1] in ALLOWED_EXTENSIONS))


def task_form():
    form = dict(name='', submitter='', ref_panel='', n_pops=3, datafile=None)
    errors = dict()
    return form, errors


def update_task_form(form, errors):
    form["title"] = request.form["name"]
    form["submitter"] = request.form["submitter"]
    form["param_reference"] = request.form["ref_panel"]
    form["param_k"] = request.form["n_pops"]
    form["data"] = request.files["datafile"]
    # Validate entry values
    if form["title"] == "":
        form["title"] = generate_name()
    if form["submitter"] == "":
        errors["submitter"] = "Missing required field"
    if form["param_reference"] not in ALLOWED_REF_PANEL:
        form["param_reference"] = ""
        errors["ref_panel"] = "Invalid reference"
    try:
        form["param_k"] = int(form["param_k"])
        if form["param_k"] < 1:
            errors["n_pops"] = "Value must be above 1"
        if form["param_k"] > 12:
            errors["n_pops"] = "Value must be below 12"
    except ValueError:
        errors["n_pops"] = "Value must be a valid number"
    if form["data"].filename == '':
        errors["datafile"] = "Missing required field"
    if not is_file_allowed(form["data"].filename):
        errors["datafile"] = "Invalid file extension"
    return form, errors


# Add date formatter
@base.app_template_filter("fmttime")
def format_datetime(date, fmt="%d/%m %H:%M:%S"):
    return date.strftime(fmt)


@base.route("/", methods=["GET"])
def home():
    tasks = list_tasks()
    return render_template("home.j2", tasks=tasks)


@base.route("/add", methods=["GET"])
def add_task():
    form, errors = task_form()
    return render_template("add.j2", task=form, error=errors)


@base.route("/add", methods=["POST"])
def create_task():
    form, errors = task_form()
    update_task_form(form, errors)
    if len(errors) == 0:
        task = submit_job(**form)
        return redirect(url_for(".view_task", id=task.id))
    return render_template("add.j2", task=form, error=errors)


@base.route("/view/<int:id>", methods=["GET"])
def view_task(id):
    task = find_task(id)
    qfile = task.q()
    plot = qfile.to_barplot()
    return render_template("view.j2", task=task, barplot=plot, ancestry=qfile)


@base.route("/view/<int:id>.out", methods=["GET"])
def download_task_out(id):
    task = find_task(id)
    return send_file(task.output_file, "text/txt")


@base.route("/view/<int:id>.log", methods=["GET"])
def download_task_log(id):
    task = find_task(id)
    return send_file(task.log_file, "text/txt")


@base.route("/view/<int:id>.q", methods=["GET"])
def download_task_q(id):
    task = find_task(id)
    return send_file(task.q_file, "text/txt")
