"""The player page and the /playlist API, with yt-dlp faked."""

import pytest
from yt_dlp.utils import DownloadError

import playlist
from conftest import watch_url


def test_the_player_page_loads(client):
    response = client.get('/')

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'const namespace = "/test";' in page
    for element in ('id="video"', 'id="request_user"', 'id="request_youtube"', 'id="broadcast_pause"',
                    'id="broadcast_play"', 'id="broadcast_mute"', 'id="disconnect"', 'id="log"'):
        assert element in page
    assert page.count('integrity="sha384-') == 4


def test_a_request_is_looked_up_queued_and_answered(client, yt):
    response = client.get('/playlist/song_request', query_string={'user': 'NatLee', 'url': 'JJo-zUi9E5U'})

    assert response.status_code == 200
    assert response.json['title'] == 'Title of JJo-zUi9E5U'
    assert response.json['url'] == watch_url('JJo-zUi9E5U')
    assert yt.calls == ['JJo-zUi9E5U']
    queued = client.get('/playlist/get_request_playlist').json
    assert [(row['user'], row['url'], row['duration']) for row in queued] == [
        ('natlee', watch_url('JJo-zUi9E5U'), 210),
    ]


def test_requesting_the_same_video_twice_answers_an_empty_list(client, yt):
    client.get('/playlist/song_request', query_string={'user': 'a', 'url': 'JJo-zUi9E5U'})

    response = client.get('/playlist/song_request', query_string={'user': 'b', 'url': watch_url('JJo-zUi9E5U')})

    assert response.json == []
    assert len(client.get('/playlist/get_request_playlist').json) == 1


def test_a_request_yt_dlp_cannot_get_answers_an_empty_list(client, yt):
    yt.error = DownloadError('ERROR: [youtube] xxxxxxxxxxx: This video is unavailable')

    response = client.get('/playlist/song_request', query_string={'user': 'a', 'url': 'xxxxxxxxxxx'})

    assert response.status_code == 200
    assert response.json == []
    assert client.get('/playlist/get_request_playlist').json == []


def test_a_request_without_a_name_is_anonymous(client, yt):
    client.get('/playlist/song_request', query_string={'url': 'JJo-zUi9E5U'})

    assert client.get('/playlist/get_request_playlist').json[0]['user'] == 'anonymous'


def test_a_link_with_an_ampersand_arrives_whole(client, yt):
    link = 'https://www.youtube.com/watch?v=JJo-zUi9E5U&t=30s'

    client.get('/playlist/add_now_video_to_default_playlist', query_string={'user': 'a', 'url': link, 'duration': '1'})

    assert client.get('/playlist/get_playlist').json[0]['url'] == link


@pytest.mark.parametrize('route', [
    '/playlist/song_request', '/playlist/ended', '/playlist/remove_request',
    '/playlist/add_now_video_to_default_playlist', '/playlist/get_yt_info',
])
def test_routes_answer_400_without_the_video(client, yt, route):
    response = client.get(route, query_string={'user': 'a', 'duration': '1'})

    assert response.status_code == 400
    assert yt.calls == []


def test_get_yt_info_answers_the_video_info(client, yt):
    response = client.get('/playlist/get_yt_info', query_string={'v': watch_url('JJo-zUi9E5U')})

    assert response.status_code == 200
    assert response.json['video_url'].startswith('https://rr1---sn-test.googlevideo.com/')
    assert response.json['ext'] == 'mp4'


def test_get_yt_info_answers_502_with_the_reason_when_yt_dlp_fails(client, yt):
    yt.error = DownloadError('ERROR: [youtube] xxxxxxxxxxx: This video is unavailable')

    response = client.get('/playlist/get_yt_info', query_string={'v': 'xxxxxxxxxxx'})

    assert response.status_code == 502
    assert 'This video is unavailable' in response.json['error']


def test_saving_to_the_default_playlist(client):
    query = {'user': 'natlee', 'url': watch_url('a'), 'duration': '30'}

    first = client.get('/playlist/add_now_video_to_default_playlist', query_string=query)
    again = client.get('/playlist/add_now_video_to_default_playlist', query_string=query)

    assert first.get_data(as_text=True) == f'{watch_url("a")} has been added into `default_playlist`.'
    assert again.get_data(as_text=True) == f'There have the same video `{watch_url("a")}` in  `default_playlist`.'
    rows = client.get('/playlist/get_playlist').json
    assert [(row['url'], row['is_request']) for row in rows] == [(watch_url('a'), False)]


def test_get_playlist_puts_requests_before_saved_videos(client, yt):
    for video_id in ('a', 'b'):
        client.get('/playlist/add_now_video_to_default_playlist',
                   query_string={'user': 'u', 'url': watch_url(video_id), 'duration': '1'})
    client.get('/playlist/song_request', query_string={'user': 'u', 'url': 'b'})

    rows = client.get('/playlist/get_playlist').json

    assert [(row['url'], row['is_request']) for row in rows] == [(watch_url('b'), True), (watch_url('a'), False)]


def test_a_finished_video_goes_to_history_and_leaves_the_requests(client, yt):
    client.get('/playlist/song_request', query_string={'user': 'u', 'url': 'a'})

    ended = client.get('/playlist/ended', query_string={'user': 'u', 'url': watch_url('a'), 'duration': '210'})
    removed = client.get('/playlist/remove_request', query_string={'url': watch_url('a')})

    assert ended.get_data(as_text=True) == f'`u` requested `{watch_url("a")}` is ended.'
    assert removed.get_data(as_text=True) == f'`{watch_url("a")}` has been removed from request.'
    assert client.get('/playlist/get_request_playlist').json == []
    with playlist.playlist_db.get_session() as session:
        from utils.db.tables import HistoryPlaylist
        assert [row.url for row in session.query(HistoryPlaylist)] == [watch_url('a')]


def test_the_queue_test_route_picks_a_demo_video(client, yt):
    response = client.get('/playlist/queue')

    assert response.status_code == 200
    assert yt.calls[0] in playlist.DEMO_QUEUE
