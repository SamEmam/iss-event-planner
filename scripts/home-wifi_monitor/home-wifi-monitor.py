from datetime import datetime
from pytz import timezone
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
ifttt_url_offline = f"https://maker.ifttt.com/trigger/away_from_home/with/key/{ifttt_key}"
ifttt_url_online = f"https://maker.ifttt.com/trigger/at_home/with/key/{ifttt_key}"

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "home_wifi_monitor_data.json")

if debug:
    data_file = "home_wifi_monitor_data.json"

tz = timezone('Europe/Copenhagen')

# Check if all devices are offline
# then trigger ifttt_url_offline
# or trigger ifttt_url_online
# Implement endpoint which triggers overwrite in case of vacation
# run async every 5min

def run_afh_check():
    home_monitor_data = json.load(open(data_file))

    now = datetime.now(tz).strftime('%m/%d/%Y, %H:%M:%S')

    if home_monitor_data['awayFromHome']:
        if home_monitor_data['Android'] == 'online' or home_monitor_data['iPhone-2'] == 'online':
            home_monitor_data['awayFromHome'] = False

            json_body = {
                "value1": home_monitor_data['Android'],
                "value2": home_monitor_data['iPhone-2'],
                "value3": home_monitor_data['awayFromHome']
            }
            r = requests.post(ifttt_url_online, json=json_body)

            print(f"IFTTT request status: {r.status_code} | Status: At Home | Datetime: {now}\n")
            with open(data_file, 'w') as json_file:
                json.dump(home_monitor_data, json_file)
    else:
        if home_monitor_data['Android'] == 'offline' and home_monitor_data['iPhone-2'] == 'offline':
            home_monitor_data['awayFromHome'] = True

            json_body = {
                "value1": home_monitor_data['Android'],
                "value2": home_monitor_data['iPhone-2'],
                "value3": home_monitor_data['awayFromHome']
            }
            r = requests.post(ifttt_url_offline, json=json_body)
            print(f"IFTTT request status: {r.status_code} | Status: Away From Home | Datetime: {now}\n")

            with open(data_file, 'w') as json_file:
                json.dump(home_monitor_data, json_file)

run_afh_check()

@aiocron.crontab('*/5 * * * *')
async def wifi_device_check():
    run_afh_check()


asyncio.get_event_loop().run_forever()
