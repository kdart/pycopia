#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Access Linux netstat information.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from socket import ntohl

from pycopia import aid

TCP_CONNECTIONS_FILE="/proc/net/tcp"

# from linux include/net/tcp_states.h
TCP_STATES = aid.Enums(TCP_ESTABLISHED=1, TCP_SYN_SENT=2, TCP_SYN_RECV=3, TCP_FIN_WAIT1=4, TCP_FIN_WAIT2=5,
        TCP_TIME_WAIT=6, TCP_CLOSE=7, TCP_CLOSE_WAIT=8, TCP_LAST_ACK=9, TCP_LISTEN=10, TCP_CLOSING=11)

(TCP_ESTABLISHED, TCP_SYN_SENT, TCP_SYN_RECV, TCP_FIN_WAIT1, TCP_FIN_WAIT2,
        TCP_TIME_WAIT, TCP_CLOSE, TCP_CLOSE_WAIT, TCP_LAST_ACK, TCP_LISTEN, TCP_CLOSING) = TCP_STATES


def itoa(address):
    return "%u.%u.%u.%u" % ((address >> 24) & 0x000000ff,
        ((address & 0x00ff0000) >> 16),
        ((address & 0x0000ff00) >> 8),
        (address & 0x000000ff))


class NetstatTCPEntry(object):
    def __init__(self, local_address, rem_address, st, queues, tr_tm_when, retrnsmt, uid, timeout, inode):
        self.local_address, self.local_port = self._split_addrport(local_address)
        self.rem_address, self.rem_port = self._split_addrport(rem_address)
        self.state = TCP_STATES.find(int(st, 16))
        self.tx_queue, self.rx_queue = [int(p, 16) for p in queues.split(":")]
        self.tr_tm_when = tr_tm_when
        self.retrnsmt = int(retrnsmt, 16)
        self.uid = int(uid)
        self.timeout = int(timeout)
        self.inode = int(inode)

    def _split_addrport(self, addrtext):
        addr_s, port_s = addrtext.split(":")
        return ntohl(int(addr_s, 16)), int(port_s, 16)


    def __str__(self):
        return "tcp  {:>15.15s}:{:5d} {:>15.15s}:{:5d} {!s}".format(
                itoa(self.local_address), self.local_port, itoa(self.rem_address), self.rem_port, self.state)



class TCPTable(object):
    """sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode"""
    def __init__(self):
        self._slots = []
#   0: 0100007F:3562 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 6296 1 ffff8801a53e93c0 99 0 0 10 -1

    def update(self):
        self._slots = slots = []
        lines = open(TCP_CONNECTIONS_FILE).readlines()
        for line in lines[1:]:
            parts = line.split()
            slots.append(NetstatTCPEntry(*parts[1:10]))

    def __str__(self):
        s = ["""Proto local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode"""]
        for nse in self._slots:
            s.append(str(nse))
        return "\n".join(s)

    def __getitem__(self, idx):
        return self._slots[idx]

    def __iter__(self):
        return iter(self._slots)

    def get_listeners(self):
        for slot in self._slots:
            if slot.state == TCP_LISTEN:
                yield slot

    def listening_on_port(self, port):
        for slot in self._slots:
            if slot.state == TCP_LISTEN and slot.local_port == port:
                return True
        return False




if __name__ == "__main__":
    tcp = TCPTable()
    tcp.update()
    print(tcp)
    print("listeners:")
    for slot in tcp.get_listeners():
        print("  ", slot)
    print("Has SSH listener? ", tcp.listening_on_port(22))
    print("Has HTTP listener? ", tcp.listening_on_port(80))
