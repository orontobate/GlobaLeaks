# -*- coding: utf-8
# Implement refresh of the list of exit nodes IPs.

from globaleaks.jobs.base import NetLoopingJob
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.utility import log
from twisted.internet.defer import inlineCallbacks


__all__ = ['ExitNodesRefreshSchedule']


class ExitNodesRefreshSchedule(NetLoopingJob):
    name = "Exit Nodes Refresh"
    interval = 3600
    threaded = False

    @inlineCallbacks
    def operation(self):
        net_agent = Settings.get_agent()
        log.debug('Fetching list of Tor exit nodes')
        yield State.tor_exit_set.update(net_agent)
        log.debug('Retrieved a list of %d exit nodes', len(State.tor_exit_set))
