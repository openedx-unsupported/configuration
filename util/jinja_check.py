#!/usr/bin/env python
import os
import sys
from jinja2 import FileSystemLoader
from jinja2 import Environment as j
from jinja2.exceptions import UndefinedError
from ansible.utils.template import _get_filters, _get_extensions
from yaml.representer import RepresenterError

input_file = sys.argv[1]

if not os.path.exists(input_file):
    print('{0}: deleted in diff'.format(input_file))
    sys.exit(0)

# Setup jinja to include ansible filters
j_e = j(trim_blocks=True, extensions=_get_extensions())
j_e.loader = FileSystemLoader(['.', os.path.dirname(input_file)])
j_e.filters.update(_get_filters())

# Go ahead and catch errors for undefined variables and bad yaml
# from `to_nice_yaml` ansible filter
try:
    j_e.from_string(file((input_file)).read()).render(func=lambda: None)
except (UndefinedError, RepresenterError), ex:
    pass
except TypeError, ex:
    if ex.message != 'Undefined is not JSON serializable':
        raise Exception(ex.message)
    pass
print('{}: ok'.format(input_file))
