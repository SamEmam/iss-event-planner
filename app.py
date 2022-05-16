from flask import request, Flask, render_template, redirect, url_for
from datetime import date

import json
import os


debug = False

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
personal_data_file = os.path.join(SITE_ROOT, data_path, "personal_event_data.json")

if debug:
    data_file = "event_data.json"
    personal_data_file = "personal_event_data.json"


def config_app(app):
    app.config["DEBUG"] = True
    app.config['SECRET_KEY'] = "hest1234"


def create_app() -> Flask:
    app = Flask(__name__)

    config_app(app)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        data = json.load(open(data_file, 'r'))
        try:
            data = sorted(data, key=lambda d: d['date'])
        except:
            print("Unable to sort dict")

        if request.method == 'POST':
            if request.form['input_button'] == 'Create event':
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_date = request.form['input_date']
                input_desc = request.form['input_desc']
                data.append({
                    "title": input_title,
                    "host": input_host,
                    "date": input_date,
                    "description": input_desc,
                    "type": "custom",
                    "creation_date": date.today().isoformat()
                })

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index'))

            elif request.form['input_button'] == 'Delete':
                input_index = int(request.form['input_index'])
                del data[input_index]

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index'))

            elif request.form['input_button'] == 'Save':
                input_index = int(request.form['input_index'])
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_date = request.form['input_date']
                input_desc = request.form['input_desc']

                data[input_index]['title'] = input_title
                data[input_index]['host'] = input_host
                data[input_index]['date'] = input_date
                data[input_index]['description'] = input_desc

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index'))

        return render_template(
            'index.html',
            data=data
        )

    @app.route('/personal', methods=['GET', 'POST'])
    def personal_calendar():
        data = json.load(open(personal_data_file, 'r'))
        try:
            data = sorted(data, key=lambda d: d['date'])
        except:
            print("Unable to sort dict")

        if request.method == 'POST':
            if request.form['input_button'] == 'Create event':
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_date = request.form['input_date']
                input_desc = request.form['input_desc']
                data.append({
                    "title": input_title,
                    "host": input_host,
                    "date": input_date,
                    "description": input_desc
                })

                json.dump(data, open(personal_data_file, 'w'))
                return redirect(url_for('personal_calendar'))

            elif request.form['input_button'] == 'Delete':
                input_index = int(request.form['input_index'])
                del data[input_index]

                json.dump(data, open(personal_data_file, 'w'))
                return redirect(url_for('personal_calendar'))

            elif request.form['input_button'] == 'Save':
                input_index = int(request.form['input_index'])
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_date = request.form['input_date']
                input_desc = request.form['input_desc']

                data[input_index]['title'] = input_title
                data[input_index]['host'] = input_host
                data[input_index]['date'] = input_date
                data[input_index]['description'] = input_desc

                json.dump(data, open(personal_data_file, 'w'))
                return redirect(url_for('personal_calendar'))

        return render_template(
            'personal.html',
            data=data
        )

    @app.after_request
    def setCORS(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001)
