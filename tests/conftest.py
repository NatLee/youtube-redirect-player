"""Shared test setup. yt-dlp is always faked, so nothing talks to YouTube."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# The app opens its database when `playlist` is imported, so point it at a
# throwaway file before any test imports the app.
os.environ['PLAYLIST_DB'] = str(Path(tempfile.mkdtemp(prefix='player-test-')) / 'playlist.db')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402
import playlist  # noqa: E402  (the module; main.playlist is the blueprint)
from utils.db.tables import DefaultPlaylist, HistoryPlaylist, RequestPlaylist  # noqa: E402


def watch_url(video_id):
    return f'https://www.youtube.com/watch?v={video_id}'


def fake_info(video_id='JJo-zUi9E5U', title='Demo video', duration=210):
    """What get_yt_info returns for a YouTube video."""
    return {
        'title': title,
        'duration': duration,
        'video_id': video_id,
        'url': watch_url(video_id),
        'video_url': f'https://rr1---sn-test.googlevideo.com/videoplayback?id={video_id}&ip=203.0.113.7',
        'ext': 'mp4',
    }


@pytest.fixture(autouse=True)
def empty_database():
    """Every test starts with three empty playlists."""
    with playlist.playlist_db.get_session() as session:
        for table in (DefaultPlaylist, RequestPlaylist, HistoryPlaylist):
            session.query(table).delete()
        session.commit()


@pytest.fixture
def client():
    main.app.config.update(TESTING=True)
    return main.app.test_client()


@pytest.fixture
def yt(monkeypatch):
    """Replace get_yt_info in the API. Set .error to make it fail; .calls lists the lookups."""

    class FakeLookup:
        def __init__(self):
            self.calls = []
            self.error = None

        def __call__(self, youtube_video_id):
            self.calls.append(youtube_video_id)
            if self.error:
                raise self.error
            video_id = youtube_video_id.rsplit('v=', 1)[-1]
            return fake_info(video_id, title=f'Title of {video_id}')

    fake = FakeLookup()
    monkeypatch.setattr(playlist, 'get_yt_info', fake)
    return fake
