# gaggle

An async-enabled requests-based Google API client.

Sorry, this requires google-api-python-client and oauth2client, but is requests
based, and this supports asyncio unlike the httplib2 transport hardwired into
the standard Google API's.

## Usage

```python

from gaggle import Client

c = Client(token=access_token, refresh_token=None)
drive = c.drive('v3')
resp = drive.files.list(q="(parents in 'root' or sharedWithMe)", fields='*')
# resp is a familiar requests-like Response object
if resp.status == 200:
    data = resp.json()
    files = data.get('files', [])
    for obj in files:
        print(obj)
>>>>
{'kind': 'drive#file',
 'id': '1ljvCC7UeyxXzI7ocB7TWroQO2NkVWUNT',
 'name': 'test.csv',
 'mimeType': 'text/csv'}
{'kind': 'drive#file',
 'id': '1khKDdTbgoJ8Ha0L7b7lZEHDMQVmJdWcg',
 'name': 'Test Folder',
 'mimeType': 'application/vnd.google-apps.folder'}
{'kind': 'drive#file',
 'id': '1Nm-Wa2yoiQKf8laTuHu_yLKq_XgqZS_K',
 'name': 'Basketball Premier League Iceland Men.xlsx',
 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
{'kind': 'drive#file',
 'id': '1Y05edI1BfvIN8R1jFYZ8-15C5PpcwPM2mp39ENGk07k',
 'name': 'Basketball Premier League Iceland Men',
 'mimeType': 'application/vnd.google-apps.spreadsheet'}

