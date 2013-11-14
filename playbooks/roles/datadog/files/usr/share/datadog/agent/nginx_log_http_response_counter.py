"""Consumes nginx access logs and emits counts by response code

Run from datadog's 'dogstreams' functionality.
"""
import re

import statsd


#SHORT_HOSTNAME = '.'.join(socket.gethostname().split('.')[:2])
MONTHS_LOOKUP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

RETURN_RE = re.compile(r'^(?:.+?) \[(?P<day>\d\d)\/(?P<month>\w\w\w)\/(?P<year>\d\d\d\d):(?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d\d) (?:[-+]\d+)\] "(?P<url>.+?)" (?P<value>\d\d\d) (?:.+)')


def count(logger, line):
    """Side-effectually count HTTP response codes by code and class.

    Inspired by http://docs.datadoghq.com/guides/logs/ - this doesn't do
    normal log event processing, but instead uses the dogstats API to do 
    simple counting. It's desirable to do it this way because we get folded
    into the agent's daemonization, and don't have to write our own or rely
    on cron.

    Every dogstream processor must accept 'logger' and 'line', even if they
    are unused in practice.
    
    Because the counting is a side-effect, every return value is None 
    (i.e., emit no events to the event stream):
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> count(logging, '10.0.0.65 - - [12/Nov/2013:06:30:53 +0000] "-" 400 0 "-" "-"')
    None
    """
    m = RETURN_RE.match(line)
    if m != None:
        statsd.statsd.increment('nginx.response.'+m.group('value')+'.count', 1)
        statsd.statsd.increment('nginx.response.'+m.group('value')[0]+'xx.count', 1)
    return None


def event_example(logger, line):
    """Do not use this method as-is; it emits events too fast.

    Inspired by http://docs.datadoghq.com/guides/logs/ - this is sample code
    that shows how to emit events into the Datadog stream based on the contents
    of the log. This method would get imported by the datadog agent, which would
    invoke it on every line of a given logfile. The returned event dictionaries
    are then sent on to dd-hq.

    Events are supposed to be special things that happen periodically, rather
    than common things we want to count a lot of. So using almost every line of
    some logfile, like this, is a really bad idea.
    
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> import pprint
    >>> pprint.pprint(event_example(logging, '10.0.0.65 - - [12/Nov/2013:06:30:53 +0000] "-" 400 0 "-" "-"'), width=40)
    {'event_type': 'http.400',
     'msg_text': '10.0.0.65 - - [12/Nov/2013:06:30:53 +0000] "-" 400 0 "-" "-"',
     'msg_title': 'nginx HTTP 400',
     'priority': 'low',
     'timestamp': 1384266653}
    >>> pprint.pprint(event_example(logging, '10.0.0.65 - - [12/Nov/2013:06:30:54 +0000] "GET /heartbeat HTTP/1.1" 200 10097 "-" "ELB-HealthChecker/1.0"'), width=40)
    {'event_type': 'http.200',
     'msg_text': '10.0.0.65 - - [12/Nov/2013:06:30:54 +0000] "GET /heartbeat HTTP/1.1" 200 10097 "-" "ELB-HealthChecker/1.0"',
     'msg_title': 'nginx HTTP 200',
     'priority': 'low',
     'timestamp': 1384266654}
    >>> pprint.pprint(event_example(logging, '10.0.0.65 - stanford [12/Nov/2013:19:35:30 +0000] "GET /courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/ HTTP/1.1" 200 11219 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"'), width=40)
    {'event_type': 'http.200',
     'msg_text': '10.0.0.65 - stanford [12/Nov/2013:19:35:30 +0000] "GET /courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/ HTTP/1.1" 200 11219 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"',
     'msg_title': 'nginx HTTP 200',
     'priority': 'low',
     'timestamp': 1384313730}

    """
    raise Exception, "Do not use this method."
    import time
    from datetime import datetime
    e = None
    m = RETURN_RE.match(line)
    
    #if m and m.group('url') != 'GET /heartbeat HTTP/1.1':
    if m and m.group('url') != 'Some arbitrary thing we want to filter out':
        e = {'msg_text': line, 'priority': 'low'}
        e['timestamp'] = int(time.mktime(datetime(
                                         month=MONTHS_LOOKUP[m.group('month')],
                                         year=int(m.group('year')),
                                         day=int(m.group('day')),
                                         hour=int(m.group('hour')),
                                         minute=int(m.group('minute')),
                                         second=int(m.group('second'))).timetuple()))
        e['msg_title'] = 'nginx HTTP ' + m.group('value')
        e['event_type'] = 'http.'+m.group('value')

    return e


if __name__ == '__main__':
    # For local testing, callable as "python /path/to/parsers.py"
    import doctest
    doctest.testmod()
