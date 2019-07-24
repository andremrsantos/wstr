import os
import datetime
import uuid
import subprocess
import logging

from enum import Enum
from peewee import SqliteDatabase, Model
from peewee import CharField, IntegerField, DateTimeField
from werkzeug.utils import secure_filename
from uwsgidecorators import spool
from .config import Config
from .job.name import generate_name
from .io import get_std_references, QFile, Reference, Genotype

REF_PANELS = get_std_references(Config.RESOURCE)

db = SqliteDatabase(Config.DB_PATH)
logger = logging.getLogger()


class EnumField(IntegerField):
    def __init__(self, choices, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        self.choices = choices

    def db_value(self, value):
        return value.value

    def python_value(self, value):
        return self.choices(value)


class Job(Model):
    class Status (Enum):
        Queued = 0
        Running = 1
        Complete = 2
        Failure = 3
        Canceled = 4
    title = CharField(default=generate_name)
    submitter = CharField(null=False)
    status = EnumField(default=Status.Queued, choices=Status)
    param_k = IntegerField(default=3)
    param_reference = CharField(default="")
    workdir = CharField(null=False)
    data_file = CharField(null=False)
    input_file = CharField(null=False)
    output_file = CharField(null=False)
    log_file = CharField(null=False)
    q_file = CharField(null=False)

    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField()

    def update_status(self, status):
        if type(status) is not Job.Status:
            raise ValueError("Invalid status value")
        self.status = status
        self.save()
        return self

    def cancel(self):
        self.status = Job.Status.Canceled
        self.save
        return self

    def q(self):
        if self.status != Job.Status.Complete:
            return QFile()
        return QFile.open(open(self.q_file, "r"))

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(Job, self).save(*args, **kwargs)

    class Meta:
        database = db


def submit_job(data, **kwargs):
    workdir = os.path.join(Config.WORK_DIR, uuid.uuid4().hex)
    while os.path.isdir(workdir):
        workdir = os.path.join(Config.WORK_DIR, uuid.uuid4().hex)
    os.mkdir(workdir)
    job = Job(
        **kwargs,
        workdir=workdir,
        data_file=os.path.join(workdir, secure_filename(data.filename)),
        input_file=os.path.join(workdir, "inputfile"),
        output_file=os.path.join(workdir, "outputfile_f"),
        log_file=os.path.join(workdir, "logfile"),
        q_file=os.path.join(workdir, "qfile"))
    data.save(job.data_file)
    job.save()
    execute_job({"id".encode("utf-8"): str(job.id).encode("utf-8")})
    return job


@spool
def execute_job(args):
    print("Processing job `%s`" % args["id"])
    job = Job.get_by_id(int(args["id"]))
    if job.status != Job.Status.Queued:
        return
    try:
        job.update_status(Job.Status.Running)

        ext = job.data_file.split(".")[-1]
        data = Genotype.parse_file(open(job.data_file, "r"), ext)
        if job.param_reference in REF_PANELS:
            ref = REF_PANELS.get(job.param_reference)
            data = Genotype.combine(ref.genotype, data)
        data.write(open(job.input_file, "w"))
        cmd = [
            Config.STRUCTURE_BIN,
            "-m", Config.MAINPARAMS,
            "-e", Config.EXTRAPARAMS,
            "-K", str(job.param_k),
            "-L", str(data.n_loci),
            "-N", str(data.n_samples),
            "-i", job.input_file,
            "-o", job.output_file[:-2]
        ]
        proc = subprocess.run(cmd, stdout=open(job.log_file, "w"), cwd=job.workdir)
        if proc.returncode != 0:
            raise ValueError("Unexpected execution error")
        qfile = QFile.parse(open(job.output_file, "r"))
        if job.param_reference != "":
            ref = REF_PANELS[job.param_reference]
            qfile.summarise(ref.groups, ref.ranges)
        qfile.write(open(job.q_file, "w"))
        job.update_status(Job.Status.Complete)
    except Exception as err:
        job.update_status(Job.Status.Failure)
        logger.error(str(err), exc_info=True)
