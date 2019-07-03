from app import app

@app.template_filter('fmttime')
def _jinja2_filter_datetime(date, fmt="%d/%m %H:%M:%S"):
    return date.strftime(fmt)