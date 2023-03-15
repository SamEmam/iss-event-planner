from dateutil.relativedelta import relativedelta
from ics import Calendar, Event
from datetime import date, datetime
from pytz import timezone
from enum import Enum

import requests
import platform
import asyncio
import aiocron
import json
import os


debug = False
if 'Microsoft' in platform.release():
    debug = True

ifttt_key = "owX5X_TKMGHZ_KOsFHPoEQlookfgtsSDsspQ1kMlcoe"
ifttt_url = f"https://maker.ifttt.com/trigger/new_event/with/key/{ifttt_key}"

strawpoll_id_padel = "bVg8o6jP1nY"
strawpoll_id_dnd = "w4nWrWaeYyA"
strawpoll_key = "5b5ac418-a0dd-11ed-8edb-cb45d087e0d2"

ical_enum = Enum(normal=0, padel=1, dnd=2)

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "event_data.json")
padel_data_file = os.path.join(SITE_ROOT, data_path, "padel_event_data.json")
settings_file = os.path.join(SITE_ROOT, data_path, "event_settings.json")
calendar_file = os.path.join(SITE_ROOT, data_path, "rumstationen.ics")
padel_calendar_file = os.path.join(SITE_ROOT, data_path, "padel.ics")
dnd_strawpoll_file = os.path.join(SITE_ROOT, data_path, "dnd_strawpoll_data.json")
dnd_calendar_file = os.path.join(SITE_ROOT, data_path, "dnd.ics")

if debug:
    data_file = "event_data.json"
    padel_data_file = "padel_event_data.json"
    settings_file = "event_settings.json"
    calendar_file = "rumstationen.ics"
    padel_calendar_file = "padel.ics"
    dnd_strawpoll_file = "dnd_strawpoll_data.json"
    dnd_calendar_file = "dnd.ics"


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
        "title": next_host,
        "host": next_host,
        "start_date": (today + relativedelta(months=+1)).isoformat(),
        "description": f"Autogenereret begivenhed for {title}.",
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
    tz = timezone('Europe/Copenhagen')

    if 'start_time' in event_data and event_data['start_time'] or 'end_time' in event_data and event_data['end_time']:
        make_all_day = False

    if make_all_day:
        event.begin = event_data['start_date']

        if 'end_date' in event_data and event_data['end_date']:
            event.end = event_data['end_date']
        event.make_all_day()

    else:
        if 'start_time' in event_data and event_data['start_time']:
            start_datetime_string = f"{event_data['start_date']} {event_data['start_time']}"
            start_datetime = tz.localize(datetime.strptime(start_datetime_string, '%Y-%m-%d %H:%M'))
            event.begin = start_datetime

        if 'end_time' in event_data and event_data['end_time']:
            if 'end_date' in event_data and event_data['end_date']:
                end_datetime_string = f"{event_data['end_date']} {event_data['end_time']}"
                end_datetime = tz.localize(datetime.strptime(end_datetime_string, '%Y-%m-%d %H:%M'))
                event.end = end_datetime

            else:
                end_datetime_string = f"{event_data['start_date']} {event_data['end_time']}"
                end_datetime = tz.localize(datetime.strptime(end_datetime_string, '%Y-%m-%d %H:%M'))
                event.end = end_datetime

    return event

def create_ical_event_padel(event_data):
    event = Event()
    event.name = f"Padel Tennis ({event_data['votes']})"

    tz = timezone('Europe/Copenhagen')

    start_datetime = tz.localize(datetime.strptime(event_data['start_date'], '%Y-%m-%d %H:%M'))
    event.begin = start_datetime

    end_datetime = tz.localize(datetime.strptime(event_data['end_date'], '%Y-%m-%d %H:%M'))
    event.end = end_datetime

    return event

def create_ical_event_dnd(event_data):
    event = Event()
    event.name = f"Dungeons & Dragons ({event_data['votes']})"

    tz = timezone('Europe/Copenhagen')

    date = tz.localize(datetime.strptime(event_data['date'], '%Y-%m-%d %H:%M'))
    event.begin = date
    event.make_all_day()

    return event

def generate_ics_file(input_file, output_file, type):
    data = json.load(open(input_file, 'r'))
    cal = Calendar()

    if type == ical_enum.normal:
        for event_data in data:
            cal.events.add(create_ical_event(event_data))
    elif type == ical_enum.padel:
        for event_data in data:
            cal.events.add(create_ical_event_padel(event_data))
    elif type == ical_enum.dnd:
        for event_data in data:
            cal.events.add(create_ical_event_dnd(event_data))
    else:
        return

    with open(output_file, 'w') as ics_file:
        ics_file.writelines(cal)


def fetch_strawpoll_data(strawpoll_id):
    url = f"https://api.strawpoll.com/v3/polls/{strawpoll_id}/results"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": strawpoll_key
    }

    response = requests.request("GET", url, headers=headers)
    strawpoll_data = response.json()

    return strawpoll_data

def interpret_strawpoll_data(strawpoll_data_file, strawpoll_data):
    strawpoll_events = []
    strawpoll_participants = []
    for participant in strawpoll_data['poll_participants']:
        name = participant['name']
        print(name)
        for i in range(len(participant['poll_votes'])):
            if participant['poll_votes'][i] == 1:
                try:
                    strawpoll_participants[i].append(name)
                except Exception:
                    strawpoll_participants.append([name])
            else:
                print(len(strawpoll_participants), i)
                if len(strawpoll_participants) <= i:
                    strawpoll_participants.append([])
    tz = timezone('Europe/Copenhagen')
    for event, participants in zip(strawpoll_data['poll_options'], strawpoll_participants):
        try:
            start_date = datetime.fromtimestamp(event['start_time'], tz)
            end_date = datetime.fromtimestamp(event['end_time'], tz)
        except Exception:
            start_date = datetime.strptime(event["date"], '%Y-%m-%d')
            end_date = datetime.strptime(event["date"], '%Y-%m-%d')
        votes = event['vote_count']
        title = start_date.strftime('%A %b %-d')
        participants = participants
        strawpoll_events.append({
            "title": title,
            "start_date": start_date.strftime('%Y-%m-%d %H:%M'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M'),
            "votes": votes,
            "participants": participants
        })
    json.dump(strawpoll_events, open(strawpoll_data_file, 'w'))


interpret_strawpoll_data(padel_data_file, fetch_strawpoll_data(strawpoll_id_padel))
interpret_strawpoll_data(dnd_strawpoll_file, fetch_strawpoll_data(strawpoll_id_dnd))

@aiocron.crontab('*/15 * * * *')
async def update_ics_file():
    generate_ics_file(data_file, calendar_file, ical_enum.normal)
    interpret_strawpoll_data(padel_data_file, fetch_strawpoll_data(strawpoll_id_padel))
    generate_ics_file(padel_data_file, padel_calendar_file, ical_enum.padel)
    interpret_strawpoll_data(dnd_strawpoll_file, fetch_strawpoll_data(strawpoll_id_dnd))
    generate_ics_file(dnd_strawpoll_file, dnd_calendar_file, ical_enum.dnd)


@aiocron.crontab('0 0 1 */2 *')
async def create_new_event():
    auto_generate_event()

asyncio.get_event_loop().run_forever()
