"""The three playlists in SQLite."""

import sqlite3

from utils import Playlist
from utils.db.tables import HistoryPlaylist


def make_playlist(tmp_path, **kwargs):
    return Playlist(database_path=str(tmp_path / 'playlist.db'), **kwargs)


def history_urls(p):
    with p.get_session() as session:
        rows = session.query(HistoryPlaylist).order_by(HistoryPlaylist.tid).all()
        return [row.url for row in rows]


def test_history_keeps_the_newest_200_records(tmp_path):
    # README: "The limit of number of records is 200." It used to stop recording
    # at 201 rows, because trimming crashed and took the new row down with it.
    p = make_playlist(tmp_path)

    for i in range(205):
        p.add_history_playlist('u', '1', f'url-{i}')

    urls = history_urls(p)
    assert len(urls) == 200
    assert urls[0] == 'url-5'
    assert urls[-1] == 'url-204'


def test_history_limit_is_configurable(tmp_path):
    p = make_playlist(tmp_path, max_number_of_history=3)

    for i in range(5):
        p.add_history_playlist('u', '1', f'url-{i}')

    assert history_urls(p) == ['url-2', 'url-3', 'url-4']


def test_requests_come_first_and_requested_defaults_are_left_out(tmp_path):
    # Three videos both saved and requested used to come back as a, b, c, b:
    # the loop deleted from the list it was walking through.
    p = make_playlist(tmp_path)
    for url in ['a', 'b', 'c']:
        p.add_default_playlist('u', '1', url)
        p.add_request_playlist('u', '1', url)
    p.add_default_playlist('u', '1', 'd')

    rows = p.get_playlist()

    assert [(row['url'], row['is_request']) for row in rows] == [
        ('a', True), ('b', True), ('c', True), ('d', False),
    ]


def test_get_playlist_without_requests_is_just_the_defaults(tmp_path):
    p = make_playlist(tmp_path)
    p.add_default_playlist('u', '1', 'a')
    p.add_request_playlist('u', '1', 'b')

    rows = p.get_playlist(load_request_playlist=False)

    assert [row['url'] for row in rows] == ['a']
    assert 'is_request' not in rows[0]


def test_get_playlist_samples_at_most_number_defaults(tmp_path):
    p = make_playlist(tmp_path)
    for i in range(10):
        p.add_default_playlist('u', '1', f'url-{i}')

    rows = p.get_playlist(number=4)

    assert len(rows) == 4
    assert len({row['url'] for row in rows}) == 4


def test_the_same_video_is_saved_and_requested_only_once(tmp_path):
    p = make_playlist(tmp_path)

    assert p.add_default_playlist('u', '1', 'https://example.com/a') is True
    assert p.add_default_playlist('v', '1', ' https://example.com/a ') is False
    assert p.add_request_playlist('u', '1', 'https://example.com/a') is True
    assert p.add_request_playlist('v', '1', 'https://example.com/a') is False

    assert len(p.get_playlist(load_request_playlist=False)) == 1
    assert len(p.get_request_playlist()) == 1


def test_a_failed_save_reports_failure(tmp_path):
    # It used to log the error and still answer True.
    p = make_playlist(tmp_path)

    assert p.add_default_playlist(None, '1', 'https://example.com/a') is False
    assert p.get_playlist(load_request_playlist=False) == []


def test_users_and_urls_are_tidied(tmp_path):
    p = make_playlist(tmp_path)

    p.add_request_playlist('  NatLee ', '210', ' https://example.com/a ')

    row = p.get_request_playlist()[0]
    assert row['user'] == 'natlee'
    assert row['url'] == 'https://example.com/a'
    assert row['duration'] == 210


def test_removing_a_request_is_saved(tmp_path):
    p = make_playlist(tmp_path)
    p.add_request_playlist('u', '1', 'a')
    p.add_request_playlist('u', '1', 'b')

    p.remove_from_request_playlist('a')

    # A second Playlist on the same file sees it too, so it was committed.
    assert [row['url'] for row in make_playlist(tmp_path).get_request_playlist()] == ['b']


def test_the_database_engine_is_made_once(tmp_path):
    p = make_playlist(tmp_path)

    with p.get_session() as first, p.get_session() as second:
        assert first.bind is second.bind


def test_a_playlist_db_from_the_first_version_still_opens(tmp_path):
    # The schema SQLAlchemy created for the original tables, written by hand.
    path = tmp_path / 'playlist.db'
    with sqlite3.connect(path) as db:
        for table in ('default_playlist', 'request_playlist', 'history_playlist'):
            db.execute(
                f'CREATE TABLE {table} (tid INTEGER NOT NULL, add_time TIMESTAMP, user VARCHAR, '
                'duration INTEGER, url VARCHAR, PRIMARY KEY (tid))'
            )
        db.execute(
            "INSERT INTO default_playlist (add_time, user, duration, url) "
            "VALUES ('2023-01-24 00:40:44.000000', 'natlee', 210, 'https://www.youtube.com/watch?v=JJo-zUi9E5U')"
        )

    p = Playlist(database_path=str(path))

    rows = p.get_playlist()
    assert [(row['user'], row['url'], row['is_request']) for row in rows] == [
        ('natlee', 'https://www.youtube.com/watch?v=JJo-zUi9E5U', False),
    ]
    assert p.add_request_playlist('u', '1', 'b') is True
