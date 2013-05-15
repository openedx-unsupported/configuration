from datetime import datetime
from contextlib import contextmanager
import sys


@contextmanager
def no_ts():
    sys.stdout.ts = False
    yield
    sys.stdout.ts = True


class TSWrapper(object):

    def __init__(self, stream):
        self.o = stream
        self.files = []
        self.files.append(self.o)
        self.newline = True
        self.ts = True

    def write(self, s):
        d = datetime.now()
        if self.ts:
            buf = ""
            lines = s.splitlines(True)

            for line in lines:
                if self.newline:
                    buf += d.strftime('[ %Y%m%d %H:%M:%S ] : {0}'.format(line))
                else:
                    buf += str(line)

                if line[-1] == '\n':
                    self.newline = True
                else:
                    self.newline = False
        else:
            buf = s

        for fh in self.files:
            fh.write(buf)
            fh.flush()

    def log_to_file(self, fn):
        fp = open(fn, 'a')
        self.files.append(fp)

    def __getattr__(self, attr):
        return getattr(self.o, attr)
