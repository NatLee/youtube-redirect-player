"""The playlist API, mounted at /playlist. Every route is a GET with query parameters."""

import os
import random

from flask import Blueprint, abort, jsonify, request
from loguru import logger
from yt_dlp.utils import DownloadError

from utils import Playlist, get_yt_info

# Where the SQLite file lives. The Docker image points PLAYLIST_DB at its /data volume.
DATABASE_PATH = os.environ.get('PLAYLIST_DB', './playlist.db')

# The name the player page sends when nobody typed one.
ANONYMOUS = 'anonymous'

# The videos the /queue test route picks from.
DEMO_QUEUE = [
    'https://www.youtube.com/watch?v=L5sbzUFHot8',
    'JJo-zUi9E5U',
    'HmWcWnPO-ns',
    'XtlDHnWgGeM',
    '7w3jBGX7UcY',
]

playlist = Blueprint('playlist_', __name__)

# The player's database.
playlist_db = Playlist(database_path=DATABASE_PATH)


def required_arg(name):
    """A query parameter the route cannot do without: answer 400 when it is missing."""
    value = request.args.get(name, '').strip()
    if not value:
        abort(400, description=f'Missing the `{name}` query parameter.')
    return value


def track_args():
    """The user, url and duration of a video, as the player page sends them."""
    return request.args.get('user') or ANONYMOUS, required_arg('url'), request.args.get('duration')


@playlist.errorhandler(DownloadError)
def yt_dlp_failed(error):
    """yt-dlp could not get the video: answer 502 with its reason."""
    logger.error(error)
    return jsonify(error=str(error)), 502


@playlist.route('/get_playlist')
def get_playlist():
    """
    從 database 實體獲取播放清單
    The requested videos first, then up to 200 shuffled default videos.
    """
    return jsonify(playlist_db.get_playlist())


@playlist.route('/get_request_playlist')
def get_request_playlist():
    """
    從 database 實體獲取當前被點播的播放清單
    The requested videos that have not finished yet.
    """
    return jsonify(playlist_db.get_request_playlist())


@playlist.route('/get_yt_info')
def get_yt_info_route():
    """
    使用 yt-dlp 來 parse 網址並獲取影片資訊（包含導向影片的網址）
    Look up a video (`v` = ID or link), including its direct file link.
    """
    return get_yt_info(required_arg('v'))


@playlist.route('/remove_request')
def remove_request():
    """
    播放器播放完成後，從播放清單中移除
    Drop a finished video from the request playlist.
    """
    url = required_arg('url')
    playlist_db.remove_from_request_playlist(url)
    return f'`{url}` has been removed from request.'


@playlist.route('/add_now_video_to_default_playlist')
def add_now_video_to_default_playlist():
    """
    添加新的影片到預設播放清單，會存取使用者名稱、網址及影片長度
    Save a video to the default playlist (user, url, duration).
    """
    user, url, duration = track_args()
    if playlist_db.add_default_playlist(user, duration, url):
        return f'{url} has been added into `default_playlist`.'
    return f'There have the same video `{url}` in  `default_playlist`.'


@playlist.route('/song_request', methods=['GET'])
def song_request():
    """
    使用者點影片，將會儲存在 database 的「請求播放清單」內
    Request a video (user, url). Answers the video's info, or [] when it is
    already requested or yt-dlp cannot get it.
    """
    user, url, _ = track_args()
    try:
        info = get_yt_info(url)
    except DownloadError as e:
        logger.error(e)
        return jsonify([])

    if playlist_db.add_request_playlist(user, info.get('duration'), info.get('url')):
        logger.info(f'`{user}` has requested `{info.get("title")}`.')
        return jsonify(info)
    return jsonify([])


@playlist.route('/ended', methods=['GET'])
def ended():
    """
    當影片結束後，將影片添加到歷史播放清單內
    Record a finished video (user, url, duration) in the history playlist.
    """
    user, url, duration = track_args()
    playlist_db.add_history_playlist(user, duration, url)
    return f'`{user}` requested `{url}` is ended.'


@playlist.route('/queue')
def playlist_queue():
    """
    測試用 queue
    Test route: the info of a random video from DEMO_QUEUE.
    """
    return get_yt_info(random.choice(DEMO_QUEUE))
