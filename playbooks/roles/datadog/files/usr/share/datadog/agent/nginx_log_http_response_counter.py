"""Consumes nginx access logs and emits counts by response code

Run from datadog's 'dogstreams' functionality.
"""
import re

import statsd


#SHORT_HOSTNAME = '.'.join(socket.gethostname().split('.')[:2])
MONTHS_LOOKUP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

RETURN_RE = re.compile(r'^(?:.+?) \[(?P<day>\d\d)\/(?P<month>\w\w\w)\/(?P<year>\d\d\d\d):(?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d\d) (?:[-+]\d+)\] "(?P<url>.+?)" (?P<value>\d\d\d) (?:.+)')


def count_event_example(logger, line):
    """Do not use this method as-is; it emits events too fast.

    Events are supposed to be special things that happen periodically, rather
    than common things we want to count a lot of. But here's a straightforward
    example that shows how to emit events based on the contents of a log file."""
    return None
    import time
    from datetime import datetime
    e = None
    m = RETURN_RE.match(line)
    
    if m and m.group('url') != 'GET /heartbeat HTTP/1.1':
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


def count(logger, line):
    """Side-effectually count HTTP response codes by code and class.

    Inspired by http://docs.datadoghq.com/guides/logs/ - this doesn't do
    normal log event processing, but instead uses the dogstats API to do 
    simple counting. It's desirable to do it this way because we get folded
    into the agent's daemonization, and don't have to write our own or rely
    on cron."""
    m = RETURN_RE.match(line)
    if m != None:
        statsd.statsd.increment('nginx.response.'+m.group('value')+'.count', 1)
        statsd.statsd.increment('nginx.response.'+m.group('value')[0]+'xx.count', 1)
    return None


### Inspired by http://docs.datadoghq.com/guides/logs/
def test():
    test_suite = [
        ('''10.0.0.65 - - [12/Nov/2013:06:30:53 +0000] "-" 400 0 "-" "-"''', 
            {'msg_text':  '10.0.0.65 - - [12/Nov/2013:06:30:53 +0000] "-" 400 0 "-" "-"',
             'priority':  'low',
             'timestamp':  1384266653,
             'msg_title':  '400',
             'event_type': '400', }),
        ('''10.0.0.65 - - [12/Nov/2013:06:30:54 +0000] "GET /heartbeat HTTP/1.1" 200 10097 "-" "ELB-HealthChecker/1.0"''', 
            {'msg_text':  '10.0.0.65 - - [12/Nov/2013:06:30:54 +0000] "GET /heartbeat HTTP/1.1" 200 10097 "-" "ELB-HealthChecker/1.0"',
             'priority':  'low',
             'timestamp':  1384266654,
             'msg_title':  '200',
             'event_type': '200', }),
        ('''10.0.0.65 - stanford [12/Nov/2013:19:35:30 +0000] "GET /courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/ HTTP/1.1" 200 11219 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"''',
            {'msg_text':  '10.0.0.65 - stanford [12/Nov/2013:19:35:30 +0000] "GET /courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/ HTTP/1.1" 200 11219 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/627b094444a1487db5c1b3caaef096cf/d8d40562b7ec40789315e2ccefa5cc5b/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"',
             'priority':  'low',
             'timestamp':  1384313730,
             'msg_title':  '200',
             'event_type': '200', }),
        ('''10.0.0.65 - stanford [12/Nov/2013:19:36:54 +0000] "GET /jsi18n/ HTTP/1.1" 200 2170 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/b5c2c03d98274010bdb655afa2eaed31/1e8b3bccf4c34f79b2e43ae64cd1f54c/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"''',
            {'msg_text':  '10.0.0.65 - stanford [12/Nov/2013:19:36:54 +0000] "GET /jsi18n/ HTTP/1.1" 200 2170 "https://stage.class.stanford.edu/courses/Education/EDUC115N/How_to_Learn_Math/courseware/b5c2c03d98274010bdb655afa2eaed31/1e8b3bccf4c34f79b2e43ae64cd1f54c/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36"', 
             'priority':  'low',
             'timestamp':  1384313814,
             'msg_title':  '200',
             'event_type': '200', }),
                ]

    # Set up the test logger
    import logging
    logging.basicConfig(level=logging.DEBUG)

    for pair in test_suite:
        actual = count_event_example(logging, pair[0])
        assert pair[1] == actual, "%s != %s" % (pair[1], actual)
        print 'test passes'


if __name__ == '__main__':
    # For local testing, callable as "python /path/to/parsers.py"
    test()
