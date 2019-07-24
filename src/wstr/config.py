import os


class Config(object):
    APP_PATH = os.getenv("APP_PATH", os.path.dirname(os.path.realpath(__file__)))
    APPLICATION_ROOT = os.getenv("APP_ROOT", "/")

    N_WORKER = os.getenv("N_WORKER", 4)
    MAX_UPLOAD_SIZE = os.getenv("MAX_UPLOAD_SIZE", 16 * 1024 * 1024)

    WORK_DIR = os.path.join(APP_PATH, "work")
    RESOURCE = os.path.join(APP_PATH, "resource")
    MAINPARAMS = os.path.join(RESOURCE, "mainparams")
    EXTRAPARAMS = os.path.join(RESOURCE, "extraparams")
    STRUCTURE_BIN = os.getenv("STRUCTURE", os.path.join(RESOURCE, "structure_src", "structure"))

    DB_PATH = os.getenv("DB", os.path.join(WORK_DIR, "wstr.db"))