#!/usr/bin/env python3

import os
import re
import sys

from collections import Counter

patterns = [
    ["Raw-SHA1",    "^[a-z_0-9]+:\{SHA\}.+"],
    ["md5crypt",  "^[a-z_0-9]+:\$1\$.{31}:[0-9]+:"],
    ["NTLM" ,     "^[a-z_0-9]+:[0-9]+:[0-9A-F]{32}:[0-9A-F]{32}:::$"],
    ["descrypt",  "^[a-z_0-9]+:.{13}:[0-9]+:.+"],
    ["bcrypt",    "^[a-z_0-9]+:\$2a\$05\$.{53}:123:[0-9]+:::::$"],
    ["Salted-SHA1",   "^[a-z_0-9]+:\{SSHA}.+"],
    ["mysql?",    "^[a-z_0-9]+:[0-9A-F]{16}$"],

]

class HD(object):
    def __init__(self):
        if len(sys.argv) != 2:
            print("Usage: hash_identifier.py <hashfile>")
            sys.exit(0)

        self.hashes = []
        with open(sys.argv[1]) as f:
            for h in f.read().splitlines():
                self.check_regexs(h)
            self.print_data()

    def check_regexs(self, h):
        for p in patterns:
            if re.match(p[1], h):
                #print(p[0], h)
                self.hashes.append(p[0])
                return
        print("Unknown match")
        print(h)
        exit(1)

    def print_data(self):
        c = Counter(self.hashes)
        #os.system("clear")
        for i in c.most_common():
            print("%s - %s" % i)


if __name__ == "__main__":
    HD()
