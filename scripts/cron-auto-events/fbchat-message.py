from messengerapi import SendApi

import requests
import json
import os


SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
data_path = "/data/"
key_file = os.path.join(SITE_ROOT, data_path, "keys.json")
key_data = json.load(open(key_file, 'r'))
fbchat_data = key_data['fbchat']


page_id = fbchat_data['page_id']
page_access_token = fbchat_data['token']

def send_message():
    send_api = SendApi(page_access_token)
    result = send_api.send_text_message("Hello World", fbchat_data['recipients']['sam'])
    print(result)


def get_recipient_id():
    # get PSID
    response = requests.get(
        f'https://graph.facebook.com/{page_id}/conversations?fields=participants&access_token={page_access_token}')

    print(response.text)