import os

from flask import request, jsonify, Flask, render_template
from injector import inject


def config_app(app):
    app.config["DEBUG"] = True


def create_app() -> Flask:
    app = Flask(__name__)

    config_app(app)


    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')


    @inject
    @app.route('/ui/womf', methods=['GET'])
    def womf_home():

        incident = servicenow_incident['number']['displayValue']
        title = servicenow_incident['u_short_description']['displayValue']
        description = cleanup_html(servicenow_incident['u_description']['displayValue'])
        resolution = cleanup_html(servicenow_incident['u_resolution_description']['displayValue'])
        date = servicenow_incident['resolved_at']['displayValue']
        users_affected = servicenow_incident['impact']['displayValue']
        response_dur = servicenow_incident['u_downtime_duration']['displayValue']

        return render_template(
            "womf_home.html",
            incident=incident,
            title=title,
            description=description,
            resolution=resolution,
            date=date,
            users_affected=users_affected,
            response_dur=response_dur,
            appkey=request.args.get('key'),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
