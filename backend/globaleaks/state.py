# -*- coding: utf-8
from twisted.python.threadpool import ThreadPool

from globaleaks import __version__
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks.utils.utility import datetime_now

class StateClass(ObjectDict):
    __metaclass__ = Singleton

    def __init__(self):
        self.orm_tp = ThreadPool(1, 1)
        self.process_supervisor = None
        self.tor_exit_set = TorExitSet()

        self.https_socks = []
        self.http_socks = []
        self.jobs = []
        self.jobs_monitor = None
        self.services = []

        self.api_token_session = None
        self.api_token_session_suspended = False

        self.RecentEventQ = []
        self.RecentAnomaliesQ = {}
        self.exceptions = {}
        self.exceptions_email_count = 0
        self.mail_counters = {}
        self.stats_collection_start_time = datetime_now()

        self.accept_submissions = True

        self.tenant_cache = {}
        self.tenant_cache[1] = ObjectDict({
            'maximum_namesize': 128,
            'maximum_textsize': 4096,
            'maximum_filesize': 30,
            'allow_iframes_inclusion': False,
            'accept_tor2web_access': {
                'admin': True,
                'whistleblower': False,
                'custodian': False,
                'receiver': False
            },
            'private': {
                'https_enabled': False,
            },
            'anonymize_outgoing_connections': True,
        })


    def get_mail_counter(self, receiver_id):
        return self.mail_counters.get(receiver_id, 0)

    def increment_mail_counter(self, receiver_id):
        self.mail_counters[receiver_id] = self.mail_counters.get(receiver_id, 0) + 1

    def reset_hourly(self):
        self.RecentEventQ[:] = []
        self.RecentAnomaliesQ.clear()
        self.exceptions.clear()
        self.exceptions_email_count = 0
        self.mail_counters.clear()
        self.stats_collection_start_time = datetime_now()


# State is a singleton class exported once
State = StateClass()
