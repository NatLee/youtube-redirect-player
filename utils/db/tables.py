"""The three playlist tables.

Table and column names are the same as in the first version, so an existing
``playlist.db`` keeps working.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.sqlite import TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Track:
    """Columns and helpers every playlist table shares."""

    tid = Column(Integer, primary_key=True)
    add_time = Column(TIMESTAMP)
    user = Column(String)
    duration = Column(Integer)
    url = Column(String)

    def __init__(self, add_time, user, duration, url):
        self.add_time = add_time
        self.user = user.strip().lower()
        self.duration = duration
        self.url = url.strip()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class DefaultPlaylist(Track, Base):
    """Videos someone saved; the player falls back to these, shuffled."""

    __tablename__ = 'default_playlist'


class RequestPlaylist(Track, Base):
    """Videos people requested and that have not finished playing yet."""

    __tablename__ = 'request_playlist'


class HistoryPlaylist(Track, Base):
    """Videos that finished playing, newest kept up to a limit."""

    __tablename__ = 'history_playlist'
