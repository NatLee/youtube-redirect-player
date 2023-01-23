
from logging import log
import random
import datetime

from loguru import logger

from sqlalchemy import create_engine, sql
from sqlalchemy.sql.expression import func

from sqlalchemy.pool import QueuePool

from sqlalchemy.orm import sessionmaker

from .tables import DefaultPlaylist, RequestPlaylist, HistoryPlaylist


def random_find_rows(session, table, sample_num):
    """
    在一次 session 中從 database table 隨機抽取一定數量(sample_num)的資料
    """
    if not sample_num:
        return []
    return session.query(table).order_by(func.random()).limit(sample_num).all()


def load_database(database_path):
    """
    讀取 sqlite 的起手式
    """

    connect_args = {
        'check_same_thread': False,
        'uri': True,
        'isolation_level': None
    }

    engine = create_engine(
        f'sqlite:///{database_path}',
        connect_args=connect_args,
        echo=False,
        poolclass=QueuePool
    )
    session = sessionmaker(bind=engine)()

    # create table if not exists
    DefaultPlaylist.metadata.create_all(engine)
    RequestPlaylist.metadata.create_all(engine)
    HistoryPlaylist.metadata.create_all(engine)

    return session


class Playlist():
    def __init__(self, database_path='./playlist.db', max_number_of_history=200):
        self.database_path = database_path
        self.max_number_of_history = max_number_of_history

    def get_session(self):
        return load_database(self.database_path)

    def get_playlist(self, number=200, load_request_playlist=True):
        session = self.get_session()
        try:
            rows = [row.as_dict() for row in random_find_rows(session, DefaultPlaylist, number)]
        except Exception as e:
            logger.error(e)
            rows = []
        finally:
            session.close()

        if load_request_playlist: # it'll arrange request playlist to first

            request_rows = self.get_request_playlist()
            for i, _ in enumerate(request_rows):
                request_rows[i]['is_request'] = True

            request_urls = [row['url'] for row in request_rows]

            for i, row in enumerate(rows):

                # add identifier for not a request
                rows[i]['is_request'] = False

                for j, request_url in enumerate(request_urls):
                    # check reduplicate
                    if row['url'] == request_url:
                        rows.pop(i)

            rows = request_rows + rows

        return rows

    def get_request_playlist(self):
        session = self.get_session()
        try:
            rows = [row.as_dict() for row in session.query(RequestPlaylist).all()]
        except Exception as e:
            logger.error(e)
            rows = []
        finally:
            session.close()
        return rows

    def remove_from_request_playlist(self, url):
        session = self.get_session()
        try:
            session.query(RequestPlaylist).filter_by(url=url).delete()
        except Exception as e:
            logger.error(e)
        finally:
            session.close()
        return

    def add_default_playlist(self, user, duration, url):
        session = self.get_session()

        exists = session.query(DefaultPlaylist).filter_by(url=url).first()

        if not exists:
            try:
                session.add(
                    DefaultPlaylist(
                        datetime.datetime.now(),
                        user,
                        duration,
                        url
                    )
                )
                session.commit()
            except Exception as e:
                logger.error(f'DefaultPlaylist :: Error occur {e}')
            finally:
                session.close()
            return True
        else:
            logger.warning(f'Default list have the same video `{url}`')
            return False

    def add_request_playlist(self, user, duration, url):

        session = self.get_session()
        exists = session.query(RequestPlaylist.url).filter_by(url=url).first()

        if not exists:
            try:
                session.add(
                    RequestPlaylist(
                        datetime.datetime.now(),
                        user,
                        duration,
                        url
                    )
                )
                session.commit()
            except Exception as e:
                logger.error(f'RequestPlaylist :: Error occur {e}')
            finally:
                session.close()
            return True
        else:
            logger.warning(f'`{user}` requests existed video `{url}`')
            return False

    def add_history_playlist(self, user, duration, url):

        session = self.get_session()

        # check max number
        number_of_history = session.query(HistoryPlaylist).count()

        try:

            if self.max_number_of_history <= number_of_history:
                d = number_of_history - self.max_number_of_history
                if d > 0:
                    last_history = session.execute(
                        sql.select(HistoryPlaylist).order_by(HistoryPlaylist.add_time.desc()).limit()
                    )
                    session.delete(last_history)

            session.add(
                HistoryPlaylist(
                    datetime.datetime.now(),
                    user,
                    duration,
                    url
                )
            )

            session.commit()

        except Exception as e:
            logger.error(f'HistoryPlaylist :: Error occur {e}')

        finally:
            session.close()

        return



# test
'''
p = Playlist('./playlist.db')
p.add_history_playlist('yyy', '100', 'tooo')
p.add_request_playlist('yyy', '100', 'tooo')
p.add_request_playlist('yyy', '100', 'tooo')
p.add_default_playlist('yyy', '100', 'tooo')
p.add_default_playlist('xxxx', '22', 'aaaaaa')
p.add_default_playlist('yyy', '100', 'tooo')
p.get_playlist()
p.get_request_playlist()
'''
