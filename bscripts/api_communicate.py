from bscripts.tricks import tech as t
import json
import os
import requests

def call_api(url):
    tmp = t.tmp_file(file_of_interest=url, hash=True, days=7, reuse=True, extension='json')
    if os.path.exists(tmp):
        with open(tmp, 'r') as f:
            rv = json.load(f)
            return rv

    response = requests.get(url, headers=t.header())
    if response.status_code == 200:
        data = response.json()

        with open(tmp, 'w') as f:
            content = json.dumps(data)
            f.write(content)

        return data

def post_api(url, data):
    tmp = t.tmp_file(file_of_interest=url + data, hash=True, days=7, reuse=True, extension='json')
    if os.path.exists(tmp):
        with open(tmp, 'r') as f:
            rv = json.load(f)
            return rv

    response = requests.request(method='post', url=url, data=data)
    if response.status_code == 200:
        rv = response.json()

        with open(tmp, 'w') as f:
            content = json.dumps(rv)
            f.write(content)

        return rv