from botocore.exceptions import ClientError
from datetime import date, timedelta, datetime

import logging

import requests
import platform
import asyncio
import aiocron
import boto3
import json
import os


debug = False
if 'Microsoft' in platform.release():
    debug = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
data_file = os.path.join(SITE_ROOT, data_path, "apod_data.json")
destination = "apod/"
apod_folder = os.path.join(SITE_ROOT, data_path, destination)
bucket = "backup.rumstationen"
apod_key = "gJcbs0l90YjhKCzskRqr0zQpPRn5gEJVwDVA4KVZ"

if debug:
    data_file = "apod_data.json"
    apod_folder = "data/apod/"

s3_client = boto3.client('s3')

def get_apod_data():
    start_date = (date.today() - timedelta(days=3)).isoformat()
    response_ok = False
    try:
        response = requests.get(f'https://api.nasa.gov/planetary/apod?thumbs=True&start_date={start_date}&api_key={apod_key}', timeout=5)
        if response.status_code == 200:
            response_ok = True
            print(response.json())
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

    json.dump(data, open(data_file, 'w'))


def download_apod_images():
    try:
        data = json.load(open(data_file, 'r'))
    except Exception:
        print("APOD data is missing, please ensure apod_data.json exists")
        return

    image_ext = data['url'].split('.')[-1]
    image = requests.get(data['url']).content

    hd_image_ext = data['hdurl'].split('.')[-1]
    hd_image = requests.get(data['hdurl']).content

    with open(f"{apod_folder}hd_image.{hd_image_ext}", 'wb') as handler:
        handler.write(hd_image)

    with open(f"{apod_folder}image.{image_ext}", 'wb') as handler:
        handler.write(image)


def get_apod_images():
    images = [_image for _image in os.listdir(apod_folder)]
    return images

def upload_apod_images(image, bucket, object_path):
    try:
        s3_client.upload_file(image, bucket, object_path)
        return True
    except ClientError as e:
        logging.error(e)
        return False

def main_loop():
    get_apod_data()
    download_apod_images()

    # Upload images to s3
    # for file_name in get_apod_images():
    #     file = os.path.join(apod_folder, file_name)
    #     result = upload_apod_images(file, bucket, f'{destination}{file_name}')
    #     print("Nasa images uploaded:", result)

main_loop()

@aiocron.crontab('0 0 * * *')
async def update_apod_data():
    main_loop()


asyncio.get_event_loop().run_forever()
