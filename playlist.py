import random

from urllib.parse import urlparse

from loguru import logger

from flask import Blueprint, jsonify, request

from utils import Playlist, get_yt_info


playlist = Blueprint('playlist_', __name__)

# 建立 player 的 database
playlist_db = Playlist(database_path='./playlist.db')


@playlist.route('/get_playlist')
def get_playlist():
    """
    從 database 實體獲取播放清單
    """
    return jsonify(playlist_db.get_playlist())

@playlist.route('/get_request_playlist')
def get_request_playlist():
    """
    從 database 實體獲取當前被點播的播放清單
    """
    return jsonify(playlist_db.get_request_playlist())

@playlist.route('/get_yt_info')
def get_yt_info_route():
    """
    使用第三方 `youtube_dl` 來 parse網址並獲取 youtube 影片資訊(包含導向影片的網址)
    """
    # TODO need to check format
    youtube_id_or_address = request.args.get('v')
    return get_yt_info(youtube_id_or_address)

@playlist.route('/remove_request')
def remove_request():
    """
    播放器播放完成後，從播放清單中移除
    """
    url = request.args.get('url')
    playlist_db.remove_from_request_playlist(url)
    return f'`{url}` has been removed from request.'

@playlist.route('/add_now_video_to_default_playlist')
def add_now_video_to_default_playlist():
    """
    添加新的影片到預設播放清單，會存取使用者名稱、網址及影片長度
    這邊考慮添加一個`影片名稱`的欄位
    """
    user = request.args.get('user')
    url = request.args.get('url')
    duration = request.args.get('duration')
    success = playlist_db.add_default_playlist(
        user,
        duration,
        url
    )

    if success:
        return f'{url} has been added into `default_playlist`.'
    else:
        return f'There have the same video `{url}` in  `default_playlist`.'

@playlist.route('/song_request', methods=['GET'])
def song_request():
    """
    使用者點影片，將會儲存在database的`請求播放清單`內
    """

    user = request.args.get('user')
    url = request.args.get('url')
    #parsed_url = urlparse(url)

    try:
        info = get_yt_info(url)

        title = info.get('title')

        success = playlist_db.add_request_playlist(
            user,
            info.get('duration'),
            info.get('url')
        )
        if success:
            logger.info(f'`{user}` has requested `{title}`.')
            return jsonify(info)
        else:
            return jsonify([])
    except Exception as e:
        logger.error(e)
        return jsonify([])

@playlist.route('/ended', methods=['GET'])
def ended():
    """
    當影片結束後，將影片添加到歷史播放清單內
    """

    user = request.args.get('user')
    url = request.args.get('url')
    duration = request.args.get('duration')

    playlist_db.add_history_playlist(
        user,
        duration,
        url
    )

    return f'`{user}` requested `{url}` is ended.'


@playlist.route('/queue')
def playlist_queue(): # test
    """
    測試用 queue
    """

    # TODO
    # get_playlist at first
    # after video played, ask next video's link

    youtube_videos = ['https://www.youtube.com/watch?v=L5sbzUFHot8', 'JJo-zUi9E5U', 'HmWcWnPO-ns', 'XtlDHnWgGeM', '7w3jBGX7UcY']
    return get_yt_info(random.choice(youtube_videos))
