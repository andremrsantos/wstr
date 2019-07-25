import os
from flask import Flask


def create_app():
    from .config import Config
    app = Flask(__name__, static_url_path=Config.APPLICATION_ROOT)
    app.config.from_object(Config)

    # Create Work directory
    if not os.path.isdir(app.config["WORK_DIR"]):
        os.mkdir(app.config["WORK_DIR"])

    from .db import Job
    Job.create_table(safe=True)

    from .views import base
    app.register_blueprint(base, url_prefix=app.config["APPLICATION_ROOT"])

    return app