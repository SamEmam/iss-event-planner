from dateutil.relativedelta import relativedelta
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
settings_file = os.path.join(SITE_ROOT, data_path, "settings.json")

if debug:
    data_file = "../../event_data.json"
    settings_file = "../../settings.json"


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


@aiocron.crontab('0 0 1 */2 *')
async def create_new_event():
    auto_generate_event()

asyncio.get_event_loop().run_forever()
