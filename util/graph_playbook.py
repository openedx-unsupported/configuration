#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import click
import yaml
from backports.functools_lru_cache import lru_cache
from pathlib2 import Path
from pygraphviz import AGraph

click.disable_unicode_literals_warning = True

DEFAULT_ROLE_DIR = (Path(__file__).parent/'../playbooks/roles').resolve()

# List of application services
SERVICES = (
    'analytics_api',
    'certs',
    'discovery',
    'ecommerce',
    'ecomworker',
    'edxapp',
    'elasticsearch',
    'forum',
    'insights',
    'memcache',
    'mongo',
    'mysql',
    'nginx',
    'notifier',
    'programs',
    'rabbitmq',
    'supervisor',
    'xqueue',
)

# DOT graph options
FONT_NAME = 'helvetica'

LABEL_SIZE = 20

LAYOUT = 'dot'

# DOT node options
OPTIONAL_SERVICE_COLOR = 'darkolivegreen1'

SERVICE_COLOR = 'cornflowerblue'

NODE_OPTIONS = dict(fontname=FONT_NAME)

# DOT edge options
EDGE_OPTIONS = dict(
    arrowsize=.5,
    dir='back',
    style='dashed',
)


def _parse_raw_list(raw_list, play, role_dir):
    """
    Parse a list of roles into `Role` objects.

    Arguments:
        raw_list (List(Union([str, Dict[str, Any]])))
        play (Play): Play to associate the role with
        role_dir (str): Directory where roles are stored

    Returns:
        List[Role]
    """
    roles = [Role(r, play, role_dir) for r in raw_list]
    return roles


class Play(object):
    """
    Ansible play.

    Attributes:
        role_dir (str): Directory where roles are stored
    """

    def __init__(self, data, role_dir):
        self._data = data
        self.role_dir = role_dir

    @property
    def _raw_roles(self):
        """
        List(Union(str, Dict(str, Any)))
        """
        return self._data['roles']

    @property
    @lru_cache(maxsize=None)
    def roles(self):
        """
        Dict(str, Role): Complete dictionary of all roles
        """
        role_list = _parse_raw_list(self._raw_roles, self, self.role_dir)
        roles = {}

        while role_list:
            role = role_list.pop(0)
            roles[role.name] = role
            role_list.extend(role.dependencies)

        return roles

    @property
    @lru_cache(maxsize=None)
    def vars(self):
        """
        Dict(str, Any): Variables defined in the play's `vars` attribute,
            as well as all the role defaults
        """
        vars = {}
        for r in self.roles.values():
            vars.update(r.defaults)
        vars.update(self._data['vars'])
        return vars

    def var_contained_by(self, cond):
        """
        Check if one of the play variables is contained in the conditional.

        Arguments:
            cond (str): The role conditional

        Returns:
            Tuple(Optional(str), Optional(Any)): The key and value
                of the matching variable
        """
        keys = [k for k in self.vars if k in cond]
        if keys:
            key = keys[0]
            return key, self.vars[key]
        else:
            return None, None


class Role(object):
    """
    Ansible role.

    Attributes:
        play (Play): Play to associate the role with
        role_dir (str): Directory where roles are stored
    """

    def __init__(self, data, play, role_dir):
        """
        Init.

        Arguments:
            name (str)
            is_optional (bool)
        """
        self._data = data
        if isinstance(data, basestring):
            self._data = {'role': data}
        self.play = play
        self.role_dir = role_dir

    def __str__(self):
        suffix = ''
        if self.is_optional:
            suffix = self._format_suffix()
        return self.name + suffix

    def _format_suffix(self):
        """
        Format optional service `self._str__` suffix.

        Returns:
            str
        """
        key, value = self.play.var_contained_by(self.when)

        if self.when in self.play.vars:
            default = bool(self.play.vars[self.when])
        elif key:
            default = "{}, {}: {}".format(self.when, key, value)

        suffix = " (default: {})".format(default)
        return suffix

    def _load_yaml(self, yaml_path):
        """
        Load and parse the designated YAML file.

        Arguments:
            yaml_path (str): Relative path to `self.role_dir`

        Returns:
            Any: Parsed result
        """
        yaml_file = Path(self.role_dir).joinpath(self.name, yaml_path)

        if not yaml_file.exists():
            return None

        with yaml_file.open() as f:
            content = yaml.safe_load(f.read())
        return content

    @property
    def color(self):
        """
        str: Background color of this role in the graph
        """
        color = 'transparent'
        if self.is_optional:
            color = OPTIONAL_SERVICE_COLOR
        elif self.is_service:
            color = SERVICE_COLOR
        return color

    @property
    @lru_cache(maxsize=None)
    def defaults(self):
        """
        Dict(str, Any): Default variables for this role
        """
        defaults = self._load_yaml('defaults/main.yml') or {}
        return defaults

    @property
    @lru_cache(maxsize=None)
    def dependencies(self):
        """
        List[Role]: Immediately dependent roles
        """
        meta = self._load_yaml('meta/main.yml')
        if meta:
            deps = _parse_raw_list(
                meta.get('dependencies', []), self.play, self.role_dir
            )
        else:
            deps = []
        return deps

    @property
    def is_optional(self):
        """
        bool: Is this role optional?
        """
        return 'when' in self._data

    @property
    def is_service(self):
        """
        bool: Is this role a service?
        """
        return self.name in SERVICES

    @property
    def name(self):
        """
        str
        """
        return self._data['role']

    @property
    def style(self):
        """
        str: Fill style of this role in the graph
        """
        if self.is_service:
            return 'filled'
        else:
            return ''

    @property
    def when(self):
        """
        str: Conditional for role
        """
        return self._data.get('when')


def _add_node(graph, node, **kwargs):
    """
    Add a node to the graph.

    **WARNING** The `graph` object is mutated by this function.

    The node will have default attributes from `NODE_OPTIONS`,
    overridable via `kwargs`.

    Arguments:
        graph (pygraphviz.AGraph)
        node (str)
        **kwargs (Any): Any valid node attributes.
    """
    options = NODE_OPTIONS.copy()
    options.update(kwargs)
    graph.add_node(node, **options)


def _echo_heading(heading):
    """
    Echo out a heading.

    Arguments:
        heading (str)
    """
    click.echo(heading)
    click.echo('-' * len(heading))


def _generate_graph_label(text, font=FONT_NAME, size=LABEL_SIZE):
    """
    Generate graph label with specified font name and size.

    Arguments:
        text (str)
        font (str)
        size (Union[int, str])

    Returns:
        str
    """
    label = '<<FONT FACE="{}" POINT-SIZE="{}">{}</FONT>>'.format(
        font, size, text
    )
    return label


def _graph_legend(graph):
    """
    Add legend to the graph.

    **WARNING** The `graph` object is mutated by this function.

    Arguments:
        graph (pygraphviz.AGraph)
    """
    for entry, color in (
            ('Service', SERVICE_COLOR),
            ('Optional Service', OPTIONAL_SERVICE_COLOR)
    ):
        _add_node(graph, entry, style='filled', fillcolor=color)


def _graph_role(graph, role, highlight_services=False):
    """
    Graph the role and its dependents.

    **WARNING** The `graph` object is mutated by this function.

    Arguments:
        graph (pygraphviz.AGraph)
        role (Role)
        highlight_services (bool): Should services defined in `SERVICES`
            be highlighted?
    """
    options = {}
    if highlight_services:
        options = dict(style=role.style, fillcolor=role.color)
    _add_node(graph, role.name, **options)

    for dep in role.dependencies:
        options = {}
        if highlight_services:
            options = dict(style=dep.style, fillcolor=dep.color)
        _add_node(graph, dep.name, **options)
        graph.add_edge(dep.name, role.name, **EDGE_OPTIONS)


def echo_services(roles):
    """
    Echo out services contained contained in the list of roles.

    Arguments:
        roles (Dict(str, Role))
    """
    relevant_roles = (k for k in roles if k in SERVICES)
    if relevant_roles:
        _echo_heading('Services')
    for k in sorted(relevant_roles):
        role = roles[k]
        click.echo("* {}".format(role))


def graph_roles(roles, outfile, playbook_path, highlight_services=False):
    """
    Generate a dependency graph based on roles provided.

    Arguments:
        roles (Dict(str, Role))
        outfile (str): Path to the output.
        playbook_path (str): Path to the playbook YAML file.
        highlight_services (bool): Whether services should be colored
            in the final output.
    """
    label = _generate_graph_label(Path(playbook_path).name)
    graph = AGraph(directed=True, label=label)

    if highlight_services:
        _graph_legend(graph)

    for k, role in roles.items():
        _graph_role(graph, role, highlight_services)

    graph.draw(outfile, prog=LAYOUT)


@click.command()
@click.argument('yaml-file', type=click.File('rb'))
@click.argument('output-file')
@click.option(
    '--role-dir',
    default=DEFAULT_ROLE_DIR.as_posix(),
    type=click.Path(exists=True),
    help="Directory where roles are stored. Default: {}".format(
        DEFAULT_ROLE_DIR
    )
)
@click.option(
    '--highlight-services', is_flag=True,
    help='Highlight predefined services in the graph.'
)
@click.option(
    '--list-services', is_flag=True,
    help='General a list of services contained in Ansible playbook.'
)
def cli(yaml_file, role_dir, output_file, highlight_services, list_services):
    """
    Graph role dependencies for an Ansible playbook.

    Output format will be determined by the extension specified.
    Not all may be available on every system depending on how
    Graphviz was built:

    ‘canon’, ‘cmap’, ‘cmapx’, ‘cmapx_np’, ‘dia’, ‘dot’, ‘fig’, ‘gd’, ‘gd2’,
    ‘gif’, ‘hpgl’, ‘imap’, ‘imap_np’, ‘ismap’, ‘jpe’, ‘jpeg’, ‘jpg’, ‘mif’,
    ‘mp’, ‘pcl’, ‘pdf’, ‘pic’, ‘plain’, ‘plain-ext’, ‘png’, ‘ps’, ‘ps2’, ‘svg’,
    ‘svgz’, ‘vml’, ‘vmlz’, ‘vrml’, ‘vtx’, ‘wbmp’, ‘xdot’, ‘xlib’

    \b
    Arguments:
        YAML_FILE: Path to the playbook YAML file.
        OUTPUT_FILE: Path to the generated graph output.
    """
    playbook = yaml.safe_load(yaml_file.read())
    # TODO: Make Playbook class?
    plays = [Play(play, role_dir) for play in playbook]
    roles = {k: v for play in plays for k, v in play.roles.items()}
    graph_roles(roles, output_file, yaml_file.name, highlight_services)
    if list_services:
        echo_services(roles)


if __name__ == '__main__':
    cli()
