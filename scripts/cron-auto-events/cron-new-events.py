from dateutil.relativedelta import relativedelta
from ics import Calendar, Event
from datetime import date

import requests
import asyncio
import aiocron
import json
import os


debug = False

ifttt_key = "owX5X_TKMGHZ_KOsFHPoEQlookfgtsSDsspQ1kMlcoe"
ifttt_url = f"https://maker.ifttt.com/trigger/new_event/with/key/{ifttt_key}"

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
personal_data_file = os.path.join(SITE_ROOT, data_path, "personal_event_data.json")
settings_file = os.path.join(SITE_ROOT, data_path, "event_settings.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")
personal_calendar_file = os.path.join(SITE_ROOT, data_path, "personal.ics")

if debug:
    data_file = "event_data.json"
    personal_data_file = "personal_event_data.json"
    settings_file = "event_settings.json"
    calendar_file = "rumstationen.ics"
    personal_calendar_file = "personal.ics"


def get_title(today):
    this_month = today
    next_month = today + relativedelta(months=+1)
    title = f"{this_month.strftime('%b')} / {next_month.strftime('%b')}"
    return title


def notify_host(phone_numbers, host, months):
    for number in phone_numbers:
        json_body = {
            "value1": number,
            "value2": host,
            "value3": months
        }
        r = requests.post(ifttt_url, json=json_body)
        print(f"IFTTT request status: {r.status_code}\njson_body: {json_body}")


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
        "start_date": (today + relativedelta(months=+1)).isoformat(),
        "description": "Autogenereret begivenhed.",
        "type": "scheduled",
        "creation_date": today.isoformat()
    })

    phone_numbers = settings_data['phone_numbers'][next_host]
    notify_host(phone_numbers, next_host, title)

    json.dump(data, open(data_file, 'w'))
    json.dump(settings_data, open(settings_file, 'w'))


def create_ical_event(event_data):
    event = Event()
    event.name = event_data['title']
    event.organizer = event_data['host']
    event.description = event_data['description'].replace('\n', '. ')

    make_all_day = True

    if 'start_time' in event_data and event_data['start_time'] or 'end_time' in event_data and event_data['end_time']:
        make_all_day = False

    if make_all_day:
        event.begin = event_data['start_date']

        if 'end_date' in event_data and event_data['end_date']:
            event.end = event_data['end_date']
        event.make_all_day()

    else:
        if 'start_time' in event_data and event_data['start_time']:
            event.begin = f"{event_data['start_date']} {event_data['start_time']}:00"

        if 'end_time' in event_data and event_data['end_time']:
            if 'end_date' in event_data and event_data['end_date']:
                event.end = f"{event_data['end_date']} {event_data['end_time']}:00"

            else:
                event.end = f"{event_data['start_date']} {event_data['end_time']}:00"

    return event


def generate_ics_file(input_file, output_file):
    data = json.load(open(input_file, 'r'))
    cal = Calendar()

    for event_data in data:
        cal.events.add(create_ical_event(event_data))

    with open(output_file, 'w') as ics_file:
        ics_file.writelines(cal)


@aiocron.crontab('*/15 * * * *')
async def update_ics_file():
    generate_ics_file(data_file, calendar_file)
    generate_ics_file(personal_data_file, personal_calendar_file)


@aiocron.crontab('0 0 1 */2 *')
async def create_new_event():
    auto_generate_event()

asyncio.get_event_loop().run_forever()
