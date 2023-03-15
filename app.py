from flask import request, Flask, render_template, redirect, url_for, send_from_directory, make_response
from appkey import require_appkey_factory
from datetime import date, timedelta, datetime
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient, Point, WritePrecision

import json
import platform
import os
import io
import requests
import hashlib
import calendar


token = "CA5cFs30OQdVs-ggNoVqlrZfLHYFtoRGUPsg-xbvt_C-8gqJA2G3KHxIMQw0q7mfoLz8aFaeM68S_KOhbCHu6A=="
org = "emamorg"
bucket = "rumstationen"
url = "http://18.198.184.123:8086"

client = InfluxDBClient(url=url, token=token)

write_api = client.write_api(write_options=SYNCHRONOUS)

debug = False
if 'Microsoft' in platform.release():
    debug = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
settings_file = os.path.join(SITE_ROOT, data_path, "event_settings.json")
padel_data_file = os.path.join(SITE_ROOT, data_path, "padel_event_data.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")
padel_calendar_file = os.path.join(SITE_ROOT, data_path, "padel.ics")
birthday_calendar_file = os.path.join(SITE_ROOT, data_path, "birthday.ics")
albums_file = os.path.join(SITE_ROOT, data_path, "albums_data.json")
thumbnails_folder = os.path.join(SITE_ROOT, data_path, "event_thumbnails")
dnd_data_file = "dnd_data.json"
dnd_thumbnails_folder = "./static/thumbnails"
dnd_strawpoll_file = os.path.join(SITE_ROOT, data_path, "dnd_strawpoll_data.json")
dnd_calendar_file = os.path.join(SITE_ROOT, data_path, "dnd.ics")

if debug:
    data_file = "event_data.json"
    settings_file = "settings.json"
    albums_file = "albums_data.json"
    calendar_file = "rumstationen.ics"
    thumbnails_folder = "./static/thumbnails"
    padel_data_file = "padel_event_data.json"
    padel_calendar_file = "padel.ics"
    dnd_data_file = "dnd_data.json"
    dnd_thumbnails_folder = "./static/thumbnails"
    birthday_calendar_file = "birthday.ics"
    dnd_strawpoll_file = "dnd_strawpoll_data.json"
    dnd_calendar_file = "dnd.ics"


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
        else:
            data[index]['hidden'] = False

    return data


def write_data_point(tag_key, tag_value, field_key, field_value):
    data_point = Point("rumstationen").tag(tag_key, tag_value).field(field_key, field_value).time(datetime.utcnow(), WritePrecision.NS)
    write_api.write(bucket, org, data_point)


def create_app() -> Flask:
    app = Flask(__name__)

    config_app(app)

    require_appkey = require_appkey_factory(app)

    @app.route('/', methods=['GET', 'POST'])
    def login():
        write_data_point("route", "login", "ip", request.remote_addr)
        if request.method == 'POST':
            pwd = hashlib.sha256(bytes(request.form['appkey'], 'utf-8')).hexdigest()[:5]
            if pwd == "0da6e":
                write_data_point("route", "login/padel", "ip", request.remote_addr)
                return redirect(url_for('padel', key=pwd))
            elif pwd == "8b38d":
                write_data_point("route", "login/dnd", "ip", request.remote_addr)
                return redirect(url_for('dnd', key=pwd))
            else:
                write_data_point("route", "login/index", "ip", request.remote_addr)
                return redirect(url_for('index', key=pwd))
        return render_template(
            'login.html',
            image_of_the_day=get_image_of_the_day())

    @app.route('/home', methods=['GET', 'POST'])
    @require_appkey
    def index():
        write_data_point("route", "home", "ip", request.remote_addr)
        data = json.load(open(data_file, 'r'))
        albums = json.load(open(albums_file, 'r'))
        settings = json.load(open(settings_file, 'r'))

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
                write_data_point("route", "home/create", "ip", request.remote_addr)
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
                write_data_point("route", "home/delete", "ip", request.remote_addr)
                input_index = int(request.form['input_index'])
                del data[input_index]

                json.dump(data, open(data_file, 'w'))
                return redirect(url_for('index', key=request.args.get('key')))

            elif request.form['input_button'] == 'Save':
                write_data_point("route", "home/update", "ip", request.remote_addr)
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
                write_data_point("route", "home/album", "ip", request.remote_addr)
                album_title = request.form['album_title']
                album_link = request.form['album_link']
                album_date = request.form['album_date']
                album_thumbnail = request.files['album_thumbnail']
                album_thumbnail.save(f"{thumbnails_folder}/{album_thumbnail.filename}")
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
            event_rot_index=settings['event_rotation_index'],
            event_rot_members=list(settings['phone_numbers'].keys()),
            albums=albums,
            thumbnails_folder=thumbnails_folder.strip('.'),
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/padel', methods=['GET'])
    @require_appkey
    def padel():
        write_data_point("route", "padel", "ip", request.remote_addr)
        data = json.load(open(padel_data_file, 'r'))

        data = hide_old_events(data, 1)

        return render_template(
            'padel.html',
            data=data,
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/dnd', methods=['GET'])
    @require_appkey
    def dnd():
        write_data_point("route", "dnd", "ip", request.remote_addr)
        char_data = json.load(open(dnd_data_file, 'r'))
        data = json.load(open(dnd_strawpoll_file, 'r'))

        return render_template(
            'dnd.html',
            data=data,
            char_data=char_data,
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/calendar/')
    def calendar_ics():
        write_data_point("route", "calendar", "ip", request.remote_addr)

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
        write_data_point("route", "calendar/padel", "ip", request.remote_addr)

        # Get the calendar data
        with io.open(padel_calendar_file, 'r', newline='\r\n') as calendar_data:
            calendar_string = calendar_data.read()

        # turn calendar data into a response
        response = app.make_response(calendar_string)
        response.headers["Content-Disposition"] = "attachment; filename=padel_calendar.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response

    @app.route('/birthday/calendar/')
    def birthday_calendar_ics():
        write_data_point("route", "calendar/birthday", "ip", request.remote_addr)

        # Get the calendar data
        with io.open(birthday_calendar_file, 'r', newline='\r\n') as calendar_data:
            calendar_string = calendar_data.read()

        # turn calendar data into a response
        response = app.make_response(calendar_string)
        response.headers["Content-Disposition"] = "attachment; filename=birthday_calendar.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response

    @app.route('/uploads/<path:filename>')
    def fetch_thumbnail(filename):
        return send_from_directory(thumbnails_folder, filename, as_attachment=True)

    @app.context_processor
    def name_to_color_processor():
        def name_to_color(name):
            sha = hashlib.sha256()
            sha.update(name.encode())
            return '#' + sha.hexdigest()[0:6]
        return dict(name_to_color=name_to_color)

    @app.context_processor
    def event_settings_processor():
        def get_event_host(rotation_index, loop_index, members):
            member_index = (int(rotation_index) + int(loop_index)) % len(members)
            event_host = members[member_index]
            month = get_event_month(loop_index)

            return {"event_host":event_host, "month":month}

        def get_event_month(loop_index):
            today = datetime.today()
            cur_month = today.month
            cur_year = today.year

            index_sum = cur_month + (loop_index * 2)
            if index_sum > 12:
                cur_year += 1

            start_month_index = index_sum % 12
            first_month = calendar.month_abbr[start_month_index]
            second_month = calendar.month_abbr[start_month_index + 1]

            month = f"[{first_month}/{second_month} {cur_year}]"
            return month
        return dict(get_event_host=get_event_host)
    

    @app.route("/<theme>/<page>/set-theme")
    @require_appkey
    def set_theme(theme="light", page="index"):
        res = make_response(redirect(url_for(page, key=request.args.get('key'))))
        res.set_cookie("theme", theme)
        return res

    @app.route("/api")
    def redirect_api():
        write_data_point("route", "api", "ip", request.remote_addr)
        return redirect('http://rumstationen.com:5000', code=301)

    @app.route("/grafana")
    def redirect_grafana():
        write_data_point("route", "grafana", "ip", request.remote_addr)
        return redirect('http://rumstationen.com:3000', code=301)

    @app.route("/influx")
    def redirect_influx():
        write_data_point("route", "influx", "ip", request.remote_addr)
        return redirect('http://rumstationen.com:8086', code=301)

    @app.after_request
    def setCORS(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001)
