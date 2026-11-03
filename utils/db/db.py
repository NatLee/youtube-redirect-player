"""SQLite storage for the default, request and history playlists."""

import datetime

from loguru import logger
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from .tables import Base, DefaultPlaylist, HistoryPlaylist, RequestPlaylist


def random_find_rows(session, table, sample_num):
    """Pick up to `sample_num` random rows from `table`."""
    if not sample_num:
        return []
    return session.query(table).order_by(func.random()).limit(sample_num).all()


def load_database(database_path):
    """Open the SQLite file (creating it and its tables if needed) and return a session factory."""
    engine = create_engine(
        f'sqlite:///{database_path}',
        # The web server answers from several threads; each gets its own connection.
        connect_args={'check_same_thread': False, 'uri': True},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


class Playlist:
    def __init__(self, database_path='./playlist.db', max_number_of_history=200):
        self.database_path = database_path
        self.max_number_of_history = max_number_of_history
        self._sessions = load_database(database_path)

    def get_session(self):
        return self._sessions()

    def get_playlist(self, number=200, load_request_playlist=True):
        """Up to `number` random default videos.

        With `load_request_playlist`, the requested videos come first (marked
        ``is_request``) and default videos that are also requested are left out.
        """
        rows = self._read(lambda session: random_find_rows(session, DefaultPlaylist, number))
        if not load_request_playlist:
            return rows

        request_rows = [dict(row, is_request=True) for row in self.get_request_playlist()]
        requested_urls = {row['url'] for row in request_rows}
        default_rows = [dict(row, is_request=False) for row in rows if row['url'] not in requested_urls]
        return request_rows + default_rows

    def get_request_playlist(self):
        return self._read(lambda session: session.query(RequestPlaylist).all())

    def remove_from_request_playlist(self, url):
        with self.get_session() as session:
            try:
                session.query(RequestPlaylist).filter_by(url=url).delete()
                session.commit()
            except Exception as e:
                logger.error(f'RequestPlaylist :: Error occur {e}')

    def add_default_playlist(self, user, duration, url):
        """Save a video unless it is already saved. Returns whether it was added."""
        return self._add_unique(DefaultPlaylist, user, duration, url)

    def add_request_playlist(self, user, duration, url):
        """Queue a request unless the same video is already queued. Returns whether it was added."""
        return self._add_unique(RequestPlaylist, user, duration, url)

    def add_history_playlist(self, user, duration, url):
        """Record a finished video, then drop the oldest records beyond the limit."""
        with self.get_session() as session:
            try:
                session.add(HistoryPlaylist(datetime.datetime.now(), user, duration, url))
                session.flush()
                newest = (
                    select(HistoryPlaylist.tid)
                    .order_by(HistoryPlaylist.add_time.desc(), HistoryPlaylist.tid.desc())
                    .limit(self.max_number_of_history)
                )
                session.execute(
                    delete(HistoryPlaylist).where(HistoryPlaylist.tid.not_in(newest)),
                    execution_options={'synchronize_session': False},
                )
                session.commit()
            except Exception as e:
                logger.error(f'HistoryPlaylist :: Error occur {e}')

    def _read(self, query):
        """Run a read query and return its rows as dicts; on a database error, log it and return []."""
        with self.get_session() as session:
            try:
                return [row.as_dict() for row in query(session)]
            except Exception as e:
                logger.error(e)
                return []

    def _add_unique(self, table, user, duration, url):
        with self.get_session() as session:
            try:
                row = table(datetime.datetime.now(), user, duration, url)
                if session.query(table.tid).filter_by(url=row.url).first():
                    logger.warning(f'{table.__tablename__} already has `{row.url}`')
                    return False
                session.add(row)
                session.commit()
                return True
            except Exception as e:
                logger.error(f'{table.__name__} :: Error occur {e}')
                return False
