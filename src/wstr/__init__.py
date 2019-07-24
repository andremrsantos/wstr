import os
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config.from_object("wstr.config.Config")

    # Create Work directory
    if not os.path.isdir(app.config["WORK_DIR"]):
        os.mkdir(app.config["WORK_DIR"])

    from .db import Job
    Job.create_table(safe=True)

    from .views import base
    app.register_blueprint(base, url_prefix=app.config["APPLICATION_ROOT"])

    return app