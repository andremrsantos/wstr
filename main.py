from app import app
from app.models import migrate_tables
from app.views import bp

# Register routes
app.register_blueprint(bp, url_prefix = app.config["APPLICATION_ROOT"])

if __name__ == "__main__":
    app.run()