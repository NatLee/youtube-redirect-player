"""Look a video up with yt-dlp."""

from yt_dlp import YoutubeDL

# What we ask yt-dlp for. "best" is the best format that already has video and
# sound in one file, so the browser's player can play it. "noplaylist" keeps a
# watch link that also carries &list=... to that one video.
YDL_OPTIONS = {
    'quiet': True,
    'forceurl': True,
    'skip_download': True,
    'noplaylist': True,
    'format': 'best',
}


def get_yt_info(youtube_video_id):
    """Return the title, duration, ID, page link, direct file link and file type of a video.

    Raises yt_dlp.utils.DownloadError when yt-dlp cannot get the video.
    """
    with YoutubeDL(YDL_OPTIONS) as yd:
        info = yd.extract_info(youtube_video_id, download=False)

    return {
        'title': info.get('title'),
        'duration': info.get('duration'),
        'video_id': info.get('id'),
        # The video's own page, e.g. https://www.youtube.com/watch?v=<id>.
        'url': info.get('webpage_url'),
        'video_url': info.get('url'),
        'ext': info.get('ext'),
    }
