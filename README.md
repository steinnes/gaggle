# gaggle

An aiohttp-based Google API client.

The google-api-python-client requirement is because this library uses it to
discover services and prepare requests, leveraging the prepare+execute pattern
underpinning the httplib2 transport.

## Usage

### JSON

```python

import asyncio
import aiohttp
from gaggle import Client


async def main():
    async with aiohttp.ClientSession() as session:
        drive = Client(
            session=session,
            token=access_token,
            # the following are optional and only required if the access_token is expired and can be refreshed
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret
        ).drive('v3')
        resp = await drive.files.list(q="parents in 'root'")
        # resp is an instance of aiohttp.ClientResponse
        if resp.status == 200:
            data = await resp.json()
            files = data.get('files', [])
            for obj in files:
                print(obj)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

```

Results in something like:
```
{'kind': 'drive#file', 'id': '...', 'name': 'test.csv', 'mimeType': 'text/csv'}
{'kind': 'drive#file', 'id': '...', 'name': 'Test Folder', 'mimeType': 'application/vnd.google-apps.folder'}
{'kind': 'drive#file', 'id': '...', 'name': 'spreadsheet.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
{'kind': 'drive#file', 'id': '...', 'name': 'spreadsheet', 'mimeType': 'application/vnd.google-apps.spreadsheet'}
```


## Installation

```
$ pip install gaggle
```

## Testing and developing

I've included a handy Makefile to make these things fairly easy.

```
$ make setup
$ make test
```
