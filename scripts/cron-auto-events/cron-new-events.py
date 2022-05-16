from dateutil.relativedelta import relativedelta
from ics import Calendar, Event
from datetime import date

import requests
import asyncio
import aiocron
import json
import os


debug = True

ifttt_key = "owX5X_TKMGHZ_KOsFHPoEQlookfgtsSDsspQ1kMlcoe"
ifttt_url = f"https://maker.ifttt.com/trigger/new_event/with/key/{ifttt_key}"

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
settings_file = os.path.join(SITE_ROOT, data_path, "event_settings.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")

if debug:
    data_file = "event_data.json"
    settings_file = "event_settings.json"
    calendar_file = "rumstationen.ics"


def get_title(today):
    today_plus_2 = today + relativedelta(months=+2)
    today_plus_3 = today + relativedelta(months=+3)
    title = f"{today_plus_2.strftime('%b')} / {today_plus_3.strftime('%b')}"
    return title


def notify_host(phone_number, host, months):
    json_body = {
        "value1": phone_number,
        "value2": host,
        "value3": months
    }
    r = requests.post(ifttt_url, json=json_body)
    print("IFTTT request status:", r.status_code)


def auto_generate_event():
    # Fetch info
    data = json.load(open(data_file, 'r'))
    settings_data = json.load(open(settings_file, 'r'))
    last_event_index = settings_data["event_rotation_index"]
    today = date.today()

    # Generate and save new data
    next_event_index = last_event_index + 1
    settings_data["event_rotation_index"] = next_event_index
    event_rotation_size = len(settings_data["event_rotation"])
    next_host_rotation_index = next_event_index % event_rotation_size
    next_host = settings_data["event_rotation"][next_host_rotation_index]

    title = get_title(today)

    data.append({
        "title": title,
        "host": next_host,
        "date": (today + relativedelta(months=+2)).isoformat(),
        "description": "Autogenereret begivenhed.",
        "type": "scheduled",
        "creation_date": today.isoformat()
    })

    phone_number = settings_data['phone_numbers'][next_host]
    notify_host(phone_number, next_host, title)

    json.dump(data, open(data_file, 'w'))
    json.dump(settings_data, open(settings_file, 'w'))


def create_ical_event(event_data):
    event = Event()
    event.name = event_data['title']
    event.organizer = event_data['host']
    event.description = event_data['description'].replace('\n', '. ')
    event.begin = event_data['date']
    return event


def generate_ics_file():
    data = json.load(open(data_file, 'r'))
    cal = Calendar()

    for event_data in data:
        cal.events.add(create_ical_event(event_data))

    with open(calendar_file, 'w') as ics_file:
        ics_file.writelines(cal)


# def strip_empty_lines():
#     with open(calendar_file, 'r') as open_file:
#         unix_content = open_file.read()

#     lines = unix_content.split("\n")

#     windows_content = ""
#     for line in lines:
#         windows_content += line + "\r\n"

#     with open(calendar_file, 'w') as open_file:
#         open_file.write(windows_content)


# def convert_line_endings():
#     # replacement strings
#     WINDOWS_LINE_ENDING = b'\r\n'
#     UNIX_LINE_ENDING = b'\n'

#     with open(calendar_file, 'rb') as open_file:
#         content = open_file.read()

#     # Unix ➡ Windows
#     content = content.replace(UNIX_LINE_ENDING, WINDOWS_LINE_ENDING)

#     with open(calendar_file, 'wb') as open_file:
#         open_file.write(content)


@aiocron.crontab('* * * * *')
async def update_ics_file():
    generate_ics_file()
    # convert_line_endings()


@aiocron.crontab('0 0 1 */2 *')
async def create_new_event():
    auto_generate_event()

asyncio.get_event_loop().run_forever()
