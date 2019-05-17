'''
Flexible Data Gathering: time_sync

This module checks the time of the host against some
NTP servers for differences bigger than 15 minutes.
'''

from __future__ import absolute_import
import logging


log = logging.getLogger(__name__)


def time_check(ntp_servers, max_offset=15, nb_servers=4,
               extend_chained=True, chained=None, chained_status=None):
    '''
    Function that queries a list of NTP servers and checks if the
    offset is bigger than `max_offset` minutes. It expects the results from
    at least `nb_servers` servers in the list, otherwise the check fails.

    The first return value is True if no error has occurred in the process and False otherwise.
    The second return value is the result of the check:
        will be True only if at least `nb_servers` servers responded and none of them had an
        offset bigger than `max_offset` minutes;
        will be False if one of the servers returned an offset bigger than `max_offset` minutes
        or if not enough servers responded to the query;

    ntp_servers
        list of strings with NTP servers to query

    max_offset
        int telling the max acceptable offset in minutes - by default is 15 minutes

    nb_servers
        int telling the min acceptable number of servers that responded to the query
        - by default 4 servers

    extend_chained
        boolean determining whether to format the ntp_servers with the chained value or not

    chained
        The value chained from the previous call
    '''
    if extend_chained:
        if chained:
            if ntp_servers:
                ntp_servers.extend(chained)
            else:
                ntp_servers = chained
    if not ntp_servers:
        log.error("No NTP servers provided")
        return False, None

    checked_servers = 0
    for ntp_server in ntp_servers:
        offset = _query_ntp_server(ntp_server)
        if not offset:
            continue
        # offset bigger than `max_offset` minutes
        if offset > max_offset * 60:
            return True, False
        checked_servers += 1
    if checked_servers < nb_servers:
        log.error("%d/%d required servers reached", checked_servers, nb_servers)
        return False, False

    return True, True


def _query_ntp_server(ntp_server):
    '''
    Query the `ntp_server`, extracts and returns the offset in seconds.
    If an error occurs, or the server does not return the expected output -
    if it cannot be reached for example - it returns None.

    ntp_server
        string containing the NTP server to query
    '''
    ret = __salt__['cmd.run']('ntpdate -q {0}'.format(ntp_server), python_shell=False)
    try:
        return float(ret.split('\n')[-1].split('offset')[1].split()[0])
    except (TypeError, AttributeError, IndexError):
        log.error("Unexpected return data %s", ret)
        return None
