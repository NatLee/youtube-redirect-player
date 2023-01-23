# Player

![image](https://user-images.githubusercontent.com/10178964/214097192-32ef6390-4481-4301-8743-98571192449f.png)

This project used to redirect Youtube videos to local server.
And its use flask and websocket as backend.
You can play video anywhere cause the playlist and history will be transferred with websocket.

## Table

`Playlist` has split into 3 tables.

播放清單被分爲 3 張表

- `DefaultPlaylist`
  Default playlist, there are videos played and stored.
  
  預設播放清單，裏面有先前存下的影片

- `RequestPlaylist`
  Request playlist, as its name. User can request videos and its will be queued up in the table.
  
  請求播放清單，使用者當下點的影片

- `HistoryPlaylist`
  History playlist. Videos played before. The limit of number of records is 200.
  
  歷史播放清單，曾經播過的影片，最大儲存 200 筆

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

Use command below and the service will start on `http://localhost:5000`.

```bash
python main.py
```

## APIs

Check these APIs in `./playlist.py`.
