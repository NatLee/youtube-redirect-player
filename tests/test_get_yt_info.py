"""get_yt_info maps what yt-dlp returns into what the player needs."""

import importlib

from utils import get_yt_info as get_yt_info_function

# utils/__init__.py re-exports the function under the module's own name, so fetch
# the module itself to swap its YoutubeDL.
get_yt_info_module = importlib.import_module('utils.get_yt_info')


class FakeYoutubeDL:
    seen = {}
    info = {
        'id': 'JJo-zUi9E5U',
        'title': 'Demo video',
        'duration': 210,
        'webpage_url': 'https://www.youtube.com/watch?v=JJo-zUi9E5U',
        'url': 'https://rr1---sn-test.googlevideo.com/videoplayback?ip=203.0.113.7',
        'ext': 'mp4',
    }

    def __init__(self, options):
        FakeYoutubeDL.seen['options'] = options

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, youtube_video_id, download):
        FakeYoutubeDL.seen['args'] = (youtube_video_id, download)
        return FakeYoutubeDL.info


def test_get_yt_info_maps_the_fields(monkeypatch):
    monkeypatch.setattr(get_yt_info_module, 'YoutubeDL', FakeYoutubeDL)

    assert get_yt_info_function('JJo-zUi9E5U') == {
        'title': 'Demo video',
        'duration': 210,
        'video_id': 'JJo-zUi9E5U',
        'url': 'https://www.youtube.com/watch?v=JJo-zUi9E5U',
        'video_url': 'https://rr1---sn-test.googlevideo.com/videoplayback?ip=203.0.113.7',
        'ext': 'mp4',
    }
    assert FakeYoutubeDL.seen['args'] == ('JJo-zUi9E5U', False)


def test_get_yt_info_asks_for_one_pre_merged_file(monkeypatch):
    monkeypatch.setattr(get_yt_info_module, 'YoutubeDL', FakeYoutubeDL)

    get_yt_info_function('JJo-zUi9E5U')

    options = FakeYoutubeDL.seen['options']
    assert options['format'] == 'best'
    assert options['noplaylist'] is True
    assert options['skip_download'] is True
