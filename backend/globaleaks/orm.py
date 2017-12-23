# -*- coding: utf-8
# orm: contains main hooks to storm ORM
# ******
import random
import threading

from storm.database import create_database
from storm.databases import sqlite
from storm.store import Store

from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool


__DB_URI = 'sqlite:'
__THREAD_POOL = None


def make_db_uri(db_file):
    return 'sqlite:' + db_file + '?foreign_keys=ON'


def set_db_uri(db_uri):
    global __DB_URI
    __DB_URI = db_uri


def get_db_uri():
    global __DB_URI
    return __DB_URI


def get_store(db_uri=None):
    if db_uri is None:
        db_uri = get_db_uri()

    return Store(create_database(db_uri))


def set_thread_pool(thread_pool):
    global __THREAD_POOL
    __THREAD_POOL = thread_pool


def get_thread_pool():
    global __THREAD_POOL
    return __THREAD_POOL


class SQLite(sqlite.Database):
    connection_factory = sqlite.SQLiteConnection

    def __init__(self, uri):
        self._filename = uri.database or ":memory:"
        self._timeout = float(uri.options.get("timeout", 30))
        self._foreign_keys = uri.options.get("foreign_keys")

    def raw_connect(self):
        raw_connection = sqlite.sqlite.connect(self._filename,
                                               timeout=self._timeout,
                                               isolation_level=None)

        if self._foreign_keys is not None:
            raw_connection.execute("PRAGMA foreign_keys = %s" %
                                   (self._foreign_keys,))

        raw_connection.execute("PRAGMA secure_delete = ON")

        return raw_connection


sqlite.SQLite = SQLite
sqlite.create_from_uri = SQLite


transact_lock = threading.Lock()


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
        with transact_lock: # pylint: disable=not-context-manager
            store = get_store()

            try:
                if self.instance:
                    result = function(self.instance, store, *args, **kwargs)
                else:
                    result = function(store, *args, **kwargs)

                store.commit()
            except:
                store.rollback()
                raise
            else:
                return result
            finally:
                store.reset()
                store.close()


class transact_sync(transact):
    def run(self, function, *args, **kwargs):
        return function(*args, **kwargs)


class TenantIterator:
    def __init__(self, resultset, limit=-1):
        self.tidmap = {}
        self.limit = limit
        self.elems = []

        for r in resultset:
            self.tidmap.setdefault(r.tid, []).append(r)

        while len(self.tidmap.keys()) > 0 and (limit <= 0 or len(self.elems) < limit):
            keys = self.tidmap.keys()
            random.shuffle(keys)
            
            for k in keys:
                try:
                    self.elems.append(self.tidmap[k].pop())
                except IndexError:
                    self.tidmap.pop(k)

    def __iter__(self):
        return self

    def next(self):
        if len(self.elems):
            return self.elems.pop(0)
        else:
            raise StopIteration
