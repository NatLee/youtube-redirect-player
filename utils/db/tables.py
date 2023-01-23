
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.sqlite import TIMESTAMP

Base = declarative_base()

class DefaultPlaylist(Base):
    __tablename__ = 'default_playlist'
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

class RequestPlaylist(Base):
    __tablename__ = 'request_playlist'
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


class HistoryPlaylist(Base):
    __tablename__ = 'history_playlist'
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