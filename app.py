from flask import request, Flask, render_template, redirect, url_for, send_from_directory
from appkey import require_appkey_factory
from datetime import date, timedelta

import json
import platform
import os
import io
import requests
import hashlib


debug = False
if 'Microsoft' in platform.release():
    debug = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
padel_data_file = os.path.join(SITE_ROOT, data_path, "padel_event_data.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")
padel_calendar_file = os.path.join(SITE_ROOT, data_path, "padel.ics")
albums_file = os.path.join(SITE_ROOT, data_path, "albums_data.json")
thumbnails_folder = os.path.join(SITE_ROOT, data_path, "event_thumbnails")

if debug:
    data_file = "event_data.json"
    albums_file = "albums_data.json"
    padel_data_file = "padel_event_data.json"
    calendar_file = "rumstationen.ics"
    padel_calendar_file = "padel.ics"
    thumbnails_folder = "./static/thumbnails"


def config_app(app):
    app.config["DEBUG"] = debug
    app.config['SECRET_KEY'] = "marc1234"
    app.config['AUTH_DISABLED'] = "0"
    app.config['UPLOAD_FOLDER'] = thumbnails_folder


def get_image_of_the_day():
    start_date = (date.today() - timedelta(days=3)).isoformat()
    data = requests.get(f'https://api.nasa.gov/planetary/apod?thumbs=True&start_date={start_date}&api_key=gJcbs0l90YjhKCzskRqr0zQpPRn5gEJVwDVA4KVZ').json()
    if 'hdurl' in data[-1]:
        return data[-1]
    elif 'hdurl' in data[-2]:
        return data[-2]
    else:
        return data[-3]


def get_title_of_the_day():
    data = requests.get('https://api.nasa.gov/planetary/apod?api_key=gJcbs0l90YjhKCzskRqr0zQpPRn5gEJVwDVA4KVZ').json()
    return data['title']


def hide_old_events(data, days):

    for index, event in enumerate(data):
        if data[index]['start_date'] < (date.today() - timedelta(days=days)).isoformat():
            data[index]['hidden'] = True
            print("Hidding", event['title'])
        else:
            data[index]['hidden'] = False

    return data


def create_app() -> Flask:
    app = Flask(__name__)

    config_app(app)

    require_appkey = require_appkey_factory(app)

    @app.route('/', methods=['GET', 'POST'])
    def login():

        if request.method == 'POST':
            pwd = hashlib.sha256(bytes(request.form['appkey'], 'utf-8')).hexdigest()[:5]
            return redirect(url_for('index', key=pwd))

        return render_template(
            'login.html',
            image_of_the_day=get_image_of_the_day())

    @app.route('/home', methods=['GET', 'POST'])
    @require_appkey
    def index():
        data = json.load(open(data_file, 'r'))
        albums = json.load(open(albums_file, 'r'))

        data = hide_old_events(data, 31)

        try:
            data = sorted(data, key=lambda d: d['start_date'])
        except Exception:
            print("Unable to sort data dict")
        try:
            albums = sorted(albums, key=lambda d: d['date'], reverse=True)
        except Exception:
            print("Unable to sort albums dict")

        if request.method == 'POST':
            if request.form['input_button'] == 'Create event':
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_desc = request.form['input_desc']
                input_start_date = request.form['input_start_date']
                input_end_date = request.form['input_end_date']
                input_start_time = request.form['input_start_time']
                input_end_time = request.form['input_end_time']
                data.append({
                    "title": input_title,
                    "host": input_host,
                    "start_date": input_start_date,
                    "end_date": input_end_date,
                    "start_time": input_start_time,
                    "end_time": input_end_time,
                    "description": input_desc,
                    "type": "custom",
                    "creation_date": date.today().isoformat()
                })

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index', key=request.args.get('key')))

            elif request.form['input_button'] == 'Delete':
                input_index = int(request.form['input_index'])
                del data[input_index]

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index', key=request.args.get('key')))

            elif request.form['input_button'] == 'Save':
                input_index = int(request.form['input_index'])
                input_title = request.form['input_title']
                input_host = request.form['input_host']
                input_desc = request.form['input_desc']
                input_start_date = request.form['input_start_date']
                input_end_date = request.form['input_end_date']
                input_start_time = request.form['input_start_time']
                input_end_time = request.form['input_end_time']

                data[input_index]['title'] = input_title
                data[input_index]['host'] = input_host
                data[input_index]['start_date'] = input_start_date
                data[input_index]['end_date'] = input_end_date
                data[input_index]['start_time'] = input_start_time
                data[input_index]['end_time'] = input_end_time
                data[input_index]['description'] = input_desc

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index', key=request.args.get('key')))

            elif request.form['input_button'] == 'Add album':
                album_title = request.form['album_title']
                album_link = request.form['album_link']
                album_date = request.form['album_date']
                album_thumbnail = request.files['album_thumbnail']
                album_thumbnail.save(f"{thumbnails_folder}/{album_thumbnail.filename}")
                print(album_title, album_link, album_thumbnail.filename)
                albums.append({
                    "title": album_title,
                    "link": album_link,
                    "date": album_date,
                    "thumbnail": album_thumbnail.filename
                })

                json.dump(albums, open(albums_file, 'w'))
                return redirect(url_for('index', key=request.args.get('key')))

        return render_template(
            'index.html',
            data=data,
            albums=albums,
            thumbnails_folder=thumbnails_folder.strip('.'),
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/padel', methods=['GET'])
    def padel_calendar():
        data = json.load(open(padel_data_file, 'r'))

        data = hide_old_events(data, 1)

        return render_template(
            'padel.html',
            data=data,
            nasa_title=get_title_of_the_day()
        )

    @app.route('/calendar/')
    def calendar():

        # Get the calendar data
        with io.open(calendar_file, 'r', newline='\r\n') as calendar_data:
            calendar_string = calendar_data.read()

        # turn calendar data into a response
        response = app.make_response(calendar_string)
        response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response

    @app.route('/padel/calendar/')
    def padel_calendar_ics():

        # Get the calendar data
        with io.open(padel_calendar_file, 'r', newline='\r\n') as calendar_data:
            calendar_string = calendar_data.read()

        # turn calendar data into a response
        response = app.make_response(calendar_string)
        response.headers["Content-Disposition"] = "attachment; filename=padel_calendar.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response

    @app.route('/uploads/<path:filename>')
    def fetch_thumbnail(filename):
        return send_from_directory(thumbnails_folder, filename, as_attachment=True)

    @app.route("/api")
    def redirect_api():
        return redirect('http://rumstationen.com:5000', code=301)

    @app.route("/grafana")
    def redirect_grafana():
        return redirect('http://rumstationen.com:3000', code=301)

    @app.route("/influx")
    def redirect_influx():
        return redirect('http://rumstationen.com:8086', code=301)

    @app.after_request
    def setCORS(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001)
