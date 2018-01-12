# -*- coding: utf-8
import random
import time


from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError

from sqlite3 import dbapi2 as sqlite
from sqlalchemy.orm import sessionmaker


from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool


__DB_URI = 'sqlite:'
__THREAD_POOL = None


def make_db_uri(db_file):
    return 'sqlite+pysqlite:////' + db_file


def set_db_uri(db_uri):
    global __DB_URI
    __DB_URI = db_uri


def get_db_uri():
    global __DB_URI
    return __DB_URI


def get_engine(db_uri=None, foreign_keys=True):
    if db_uri is None:
        db_uri = get_db_uri()

    engine = create_engine(db_uri, module=sqlite, connect_args={'timeout': 30}, poolclass=QueuePool, pool_size=16)

    if foreign_keys:
        def on_connect(conn, record):
            conn.execute('pragma foreign_keys=ON')

        event.listen(engine, 'connect', on_connect)

    return engine



def get_session(db_uri=None):
    engine  = get_engine(db_uri)
    session = sessionmaker(bind=engine)
    return session()


def set_thread_pool(thread_pool):
    global __THREAD_POOL
    __THREAD_POOL = thread_pool


def get_thread_pool():
    global __THREAD_POOL
    return __THREAD_POOL


class transact(object):
    """
    Class decorator for managing transactions.
    """
    def __init__(self, method):
        self.method = method
        self.instance = None

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    def run(self, function, *args, **kwargs):
        return deferToThreadPool(reactor,
                                 get_thread_pool(),
                                 function,
                                 *args,
                                 **kwargs)

    def _wrap(self, function, *args, **kwargs):
        """
        Wrap provided function calling it inside a thread and
        passing the store to it.
        """
        session = get_session()

        try:
            while True:
                try:
                    if self.instance:
                        result = function(self.instance, session, *args, **kwargs)
                    else:
                        result = function(session, *args, **kwargs)

                    session.commit()
                except OperationalError as e:
                    session.rollback()

                    if "database is locked" not in str(e):
                        raise

                    time.sleep(0.1)
                except Exception:
                    session.rollback()
                    raise
                else:
                    return result
        finally:
            session.close()


class transact_sync(transact):
    def run(self, function, *args, **kwargs):
        return function(*args, **kwargs)
