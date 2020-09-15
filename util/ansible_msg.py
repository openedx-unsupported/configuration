#!/usr/bin/env python
"""Simple utility for deciphering Ansible jsonized task output."""

from __future__ import print_function

import json
import sys

if len(sys.argv) > 1:
    f = open(sys.argv[1])
else:
    if sys.stdin.isatty():
        print("Copy one complete line of junk from ansible output, and pipe it to me.")
        sys.exit()
    f = sys.stdin

junk = f.read()
if not junk:
    print("No message to decode.")
    sys.exit()

# junk:
# '==> default: failed: [localhost] (item=/edx/app/edx_ansible/edx_ansible/requirements.txt) => {"cmd": "/edx/app/edx...'

junk = junk.replace('\n', '')
junk = junk[junk.index('=> {')+3:]
junk = junk[:junk.rindex('}')+1]

data = json.loads(junk)

# Order these so that the most likely useful messages are last.
GOOD_KEYS = ['cmd', 'module_stdout', 'module_stderr', 'warnings', 'msg', 'censored', 'stderr', 'stdout']
IGNORE_KEYS = ['stdout_lines', 'stderr_lines', 'start', 'end', 'delta', 'changed', 'failed', 'rc', 'item']

unknown_keys = set(data) - set(GOOD_KEYS) - set(IGNORE_KEYS)
if unknown_keys:
    print("== Unknown keys ======================")
    for key in unknown_keys:
        print("{key}: {val!r:80}".format(key=key, val=data[key]))

for key in GOOD_KEYS:
    if data.get(key):
        print("== {key} ===========================".format(key=key))
        print((data[key]))
