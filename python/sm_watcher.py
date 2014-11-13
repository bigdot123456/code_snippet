#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Usage: ./prog board_name keyword
# By default, it will show all articles at the couponslife board of newsmth
# Maintained at
# https://github.com/yeasy/code_snippet/blob/master/python/sm_watcher.py

import random
import re
import signal
import sys
import threading
import time
import urllib2


headers_pool = [
    {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; \
                   rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
    {'User-Agent': 'Mozilla/5.0 (compatible;MSIE 9.0; Windows NT 6.1; \
                   Trident/5.0)'},
    {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;) '
                   'AppleWebKit/534.50(KHTML, like Gecko) Version/5.1; \
                   Safari/534.50'}
]

DEFAULT_BOARD = 'couponslife'
DEFAULT_KEYWORD = ".*"
DEFAULT_URL = "http://www.newsmth.net/bbsdoc.php?board=%s&ftype=6" % \
              DEFAULT_BOARD
DEFAULT_PREFIX = "http://www.newsmth.net/bbstcon.php?board=%s&gid=" % \
                 DEFAULT_BOARD


def get_time_str(ticks=None, str_format='%H:%M:%S'):
    """
    Get the time string of given ticks or now
    :param ticks: ticks to convert
    :param str_format: Output based on the str_format
    :return:
    """
    t = ticks or time.time()
    return time.strftime(str_format, time.localtime(t))


class BoardWatcher(threading.Thread, object):
    """
    Watcher for a given board, will keep printing new articles with keyword.
    This class is easily implemented based on Threading.Thread or
    Multiprocessing.Process, but now it seems not necessary.
    """

    def __init__(self, board_name=DEFAULT_BOARD, title_keyword=DEFAULT_KEYWORD):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.board = board_name
        self.keyword = title_keyword
        self.url = DEFAULT_URL.replace(DEFAULT_BOARD, self.board)
        self.ct_prefix = DEFAULT_PREFIX.replace(DEFAULT_BOARD, self.board)
        self.coding = sys.getfilesystemencoding()

    def run(self):
        print 'board=%s, keyword=%s' % (self.board, self.keyword)
        print "###### start at ", get_time_str(str_format='%Y-%m-%d %H:%M:%S')
        last_gid = 0
        while True:
            entries_new = self.get_board()
            if not entries_new:
                continue
            entries_new.sort(key=lambda x: x[3])  # based on gid
            hit_entries = filter(lambda x: x[3] > last_gid,
                                 entries_new)
            if last_gid < entries_new[-1][3]:
                last_gid = entries_new[-1][3]
            self.print_out(hit_entries)
            time.sleep(random.uniform(1, 7))

    def get_board(self):
        """
        Return articles collection on board,
        in format of [[gid,id,ts,title],...]
        :return: article list or []
        """
        if not self.board:
            return
        now = time.time()
        result = []
        pat = re.compile(u"c.o\(.*?\);", re.UNICODE)
        page = self.get_page()
        if not page:
            return []
        content = page.decode('gb18030', 'ignore')
        entries = re.findall(pat, content)
        for e in entries:
            f = e.split(',')
            ts, title, uid, gid = int(f[4]), f[5], f[2], f[1]
            title, uid = title.strip("' "), uid.strip("' ")
            if uid != 'deliver' and now - ts < 3600:  # only in recent hour
                if self.keyword and re.search(self.keyword, title):
                    result.append([ts, title, uid, gid])
        return result

    def get_page(self):
        """
        Get the page content of given url.
        :return: page or None
        """
        if not self.url:
            return None
        headers = headers_pool[random.randint(0, len(headers_pool)-1)]
        try:
            req = urllib2.Request(url=self.url, headers=headers)
            response = urllib2.urlopen(req, timeout=5)
            return response.read()
        except Exception:
            return None

    def print_out(self, entries):
        """
        Out put the interested entries: [ts, title, uid, gid ]
        :param entries: Entries to print_out
        :return:
        """
        for e in entries:
            print '%s %s\t %s %s' % (get_time_str(e[0]), e[1], e[2],
                                     self.ct_prefix+e[3])


def signal_handler(signal_num, frame):
    print 'You pressed Ctrl+C!'
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        board, keyword = DEFAULT_BOARD, DEFAULT_KEYWORD
    else:
        board, keyword = sys.argv[1], sys.argv[2]

    signal.signal(signal.SIGINT, signal_handler)

    p = BoardWatcher(board, keyword)
    p.start()

    while True:
        time.sleep(1)
