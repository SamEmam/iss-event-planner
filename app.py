from flask import request, Flask, render_template, redirect, url_for, send_from_directory, make_response, session
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
apod_key = "gJcbs0l90YjhKCzskRqr0zQpPRn5gEJVwDVA4KVZ"

client = InfluxDBClient(url=url, token=token)

write_api = client.write_api(write_options=SYNCHRONOUS)

debug = False
if 'microsoft' in platform.release().lower():
    debug = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
settings_file = os.path.join(SITE_ROOT, data_path, "event_settings.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")
birthday_calendar_file = os.path.join(SITE_ROOT, data_path, "birthday.ics")

padel_data_file = os.path.join(SITE_ROOT, data_path, "padel_event_data.json")
padel_calendar_file = os.path.join(SITE_ROOT, data_path, "padel.ics")

albums_file = os.path.join(SITE_ROOT, data_path, "albums_data.json")
thumbnails_folder = os.path.join(SITE_ROOT, data_path, "event_thumbnails")

dnd_data_file = "dnd_data.json"
dnd_thumbnails_folder = "./static/thumbnails"
dnd_strawpoll_file = os.path.join(SITE_ROOT, data_path, "dnd_strawpoll_data.json")
dnd_calendar_file = os.path.join(SITE_ROOT, data_path, "dnd.ics")

hof_file = "hof_data.json"

if debug:
    data_file = "event_data.json"
    settings_file = "settings.json"
    calendar_file = "rumstationen.ics"
    birthday_calendar_file = "birthday.ics"

    padel_data_file = "padel_event_data.json"
    padel_calendar_file = "padel.ics"

    albums_file = "albums_data.json"
    thumbnails_folder = "./static/thumbnails"

    dnd_data_file = "dnd_data.json"
    dnd_thumbnails_folder = "./static/thumbnails"
    dnd_strawpoll_file = "dnd_strawpoll_data.json"
    dnd_calendar_file = "dnd.ics"

    hof_file = "hof_data.json"


def config_app(app):
    app.config["DEBUG"] = debug
    app.config['SECRET_KEY'] = "marc1234"
    app.config['AUTH_DISABLED'] = "0"
    app.config['UPLOAD_FOLDER'] = thumbnails_folder


def get_image_of_the_day():
    start_date = (date.today() - timedelta(days=3)).isoformat()
    response_ok = False
    try:
        response = requests.get(f'https://api.nasa.gov/planetary/apod?thumbs=True&start_date={start_date}&api_key={apod_key}', timeout=2)
        if response.status_code == 200:
            response_ok = True
    except Exception:
        print("Nasa APOD is down", datetime.today())

    if response_ok:
        data = response.json()
        if 'hdurl' in data[-1]:
            return data[-1]
        elif 'hdurl' in data[-2]:
            return data[-2]
        else:
            return data[-3]
    else:
        data = {
            'hdurl': 'https://apod.nasa.gov/apod/image/2306/Trifid_Pugh_2346.jpg',
            'url': 'https://apod.nasa.gov/apod/image/2306/Trifid_Pugh_1080.jpg',
            'title': 'Astronomy Picture Of the Day'
        }
        return data


def get_title_of_the_day():
    response_ok = False
    try:
        response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={apod_key}', timeout=1)
        if response.status_code == 200:
            response_ok = True
    except Exception:
        print("Nasa APOD is down", datetime.today())

    if response_ok:
        data = response.json()
        return data['title']
    else:
        return 'Astronomy Picture Of the Day'


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

        data = hide_old_events(data, 16)

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

        pwd = request.args.get('key')
        if pwd == "0da6e":
            lock_user_to_site = True
        else:
            lock_user_to_site = False

        return render_template(
            'padel.html',
            data=data,
            lock_user_to_site=lock_user_to_site,
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/dnd', methods=['GET'])
    @require_appkey
    def dnd():
        write_data_point("route", "dnd", "ip", request.remote_addr)
        char_data = json.load(open(dnd_data_file, 'r'))
        data = json.load(open(dnd_strawpoll_file, 'r'))

        pwd = request.args.get('key')
        if pwd == "8b38d":
            lock_user_to_site = True
        else:
            lock_user_to_site = False

        return render_template(
            'dnd.html',
            data=data,
            char_data=char_data,
            lock_user_to_site=lock_user_to_site,
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/hof', methods=['GET'])
    @require_appkey
    def hof():
        write_data_point("route", "hof", "ip", request.remote_addr)
        data = json.load(open(hof_file, 'r'))

        return render_template(
            'hof.html',
            data=data,
            appkey=request.args.get('key'),
            nasa_title=get_title_of_the_day()
        )

    @app.route('/dungeonmaster', methods=['GET'])
    @require_appkey
    def dungeon_master():
        write_data_point("route", "dungeonmaster", "ip", request.remote_addr)

        pwd = request.args.get('key')
        if pwd == "8b38d":
            lock_user_to_site = True
        else:
            lock_user_to_site = False

        return render_template(
            'dungeon_master.html',
            lock_user_to_site=lock_user_to_site,
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

    @app.route('/dnd/calendar/')
    def dnd_calendar_ics():
        write_data_point("route", "calendar/dnd", "ip", request.remote_addr)

        # Get the calendar data
        with io.open(dnd_calendar_file, 'r', newline='\r\n') as calendar_data:
            calendar_string = calendar_data.read()

        # turn calendar data into a response
        response = app.make_response(calendar_string)
        response.headers["Content-Disposition"] = "attachment; filename=dnd_calendar.ics"
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
            dnd_name_color_dict = {
                "Mithras": "#e84141",
                "Theren": "#62b53a",
                "Reimruk": "#e5623e",
                "Iris": "#c361ff",
                "Bob2": "#3a70e2",
            }
            if name in dnd_name_color_dict.keys():
                return dnd_name_color_dict[name]
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

            return {"event_host": event_host, "month": month}

        def get_event_month(loop_index):
            today = datetime.today()
            cur_month = today.month
            cur_year = today.year

            index_sum = cur_month + (loop_index * 2)
            if index_sum > 12:
                cur_year += 1

            start_month_index = index_sum % 12
            if start_month_index == 0:
                start_month_index = 12

            month_offset = ((start_month_index) % 2) - 1
            first_month = calendar.month_abbr[start_month_index + month_offset]
            second_month = calendar.month_abbr[start_month_index + 1 + month_offset]

            month = f"[{first_month}/{second_month} {cur_year}]"
            return month
        return dict(get_event_host=get_event_host)

    @app.route("/<theme>/<page>/set-theme")
    @require_appkey
    def set_theme(theme="light", page="index"):
        res = make_response(redirect(url_for(page, key=request.args.get('key'))))
        res.set_cookie("theme", value=theme, max_age=(60 * 60 * 24 * 365 * 2))
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

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @app.after_request
    def setCORS(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001)
