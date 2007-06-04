#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import socket, string, sys

def split_and_remove_quotes(str):
    pos = string.find(str, " ")
    return (str[ : pos], str[pos + 2 : -1])

class DictError(Exception):
    
    def __init__(self, msg, code):
        self._code = code

    def get_code(self):
        return self._code

class DictConnection(object):

    def __init__(self, server, port = 2628, identify = 1):
        self._server = server
        self._port = port
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((socket.gethostbyname(self._server),
                              self._port))
        self._conn.recv(1024) # eat welcome message

#          if identify:
#              self._send("CLIENT dict.py/0.00", 1)

    def get_databases(self):
        return map(split_and_remove_quotes,
                   self._interpret_multiline(self._send("SHOW DATABASES")))

    def get_strategies(self):
        return map(split_and_remove_quotes,
                   self._interpret_multiline(self._send("SHOW STRAT")))

    def get_database_info(self, db):
        return self._interpret_multiline(self._send("SHOW INFO %s" % db))

    def get_server_info(self):
        return self._interpret_multiline(self._send("SHOW SERVER"), "\r\n")
    
    def get_definition(self, word, db = "*"):
        try:
            return self._interpret_multiresp(self._send("DEFINE %s %s" %
                                                        (db, word),
                                                        "\r\n.\r\n250"))
        except DictError, e:
            if e.get_code() == 552:
                return []

            raise

    def get_words(self, search, db = "*", strategy = "prefix"):
        try:
            return map(split_and_remove_quotes,
                       self._interpret_multiline(self._send("MATCH %s %s %s" %
                                                     (db, strategy, search))))
        except DictError, e:
            if e.get_code() == 552:
                return []

            raise
    
    def _send(self, cmd, resp_term = "\r\n.\r\n"):
        self._conn.send(cmd + "\r\n")
        self._verify(self._conn.recv(1024 * 16))
        return self._receive_response(resp_term)

    def _verify(self, resp):
        if resp[0] < "1" or resp[0] > "3":
            raise DictError(resp[4 : ], int(resp[ : 3]))

    def _interpret_multiline(self, resp):
        lines = string.split(resp, "\r\n")
        return lines[ : lines.index(".")]

    def _interpret_multiresp(self, resp):
        resps = []
        lines = []
        for line in string.split(resp, "\r\n"):
            if line == ".":
                resps.append(lines)
                lines = []
            else:
                lines.append(line)
                    
        return resps

    def _receive_response(self, look_for):
        resp = self._conn.recv(1024 * 16)
        while string.find(resp, look_for) == -1:
            resp = resp + self._conn.recv(1024 * 16)

        return resp
    
# ---

if __name__ == "__main__":
    from pprint import pprint
    ds = DictConnection("dict.org")  # "127.0.0.1") 

    if len(sys.argv) > 1:
        word = sys.argv[1]
    else:
        word = "lambda"

    #pprint(ds.get_server_info())
    #pprint(ds.get_database_info(word))
    #pprint(ds.get_databases())
    #pprint(ds.get_strategies())
    pprint(ds.get_definition(word))
    #pprint(ds.get_words(word))
