import sys
from contextlib import contextmanager
from fabric.api import puts

class SquelchingStream(object):
    def __init__(self, stream):
        self.__dict__['stream'] = stream
        self.__dict__['squelched'] = False
        self.__dict__['needs_line_ending'] = False

    def write(self, string):
        if self.squelched:
            self.stream.write('.')
            self.stream.flush()
            self.needs_line_ending = True
        else:
            if self.needs_line_ending:
                self.needs_line_ending = False
                self.stream.write('\n')
            self.stream.write(string)

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def __setattr__(self, attr, val):
        if attr in self.__dict__:
            return object.__setattr__(self, attr, val)

        return setattr(self.stream, attr, val)

sys.stdout = SquelchingStream(sys.stdout)
sys.stderr = SquelchingStream(sys.stderr)

def squelch():
    sys.stdout.squelched = sys.stderr.squelched = True

def unsquelch():
    sys.stdout.squelched = sys.stderr.squelched = False

@contextmanager
def unsquelched(stream=sys.stdout):
    old_state = stream.squelched
    stream.squelched = False
    yield
    stream.squelched = old_state

def notify(msg, show_prefix=None, end='\n', flush=False):
    with unsquelched():
        puts(msg, show_prefix, end, flush)
