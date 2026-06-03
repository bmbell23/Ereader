import requests
import os
import json
from requests.auth import HTTPDigestAuth

username = os.environ.get('CALIBRE_USERNAME')
password = os.environ.get('CALIBRE_PASSWORD')
url = "http://localhost:8083/cdb/set-fields/432/library"

data = {
    "changes": {"title": "The Blade Itself"},
    "loaded_book_ids": [432]
}

print(f"Connecting to {url} as {username}...")
try:
    r = requests.post(url, json=data, auth=HTTPDigestAuth(username, password), timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Response Headers: {dict(r.headers)}")
    print(f"Response Body: {r.text}")
except Exception as e:
    print(f"Error: {e}")
