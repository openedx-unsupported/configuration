from __future__ import absolute_import
from __future__ import print_function
import os
import pathlib2
import logging
import yaml
import sys
import networkx as nx
from collections import namedtuple
import argparse
import six

TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR")
DOCKER_PATH_ROOT = pathlib2.Path(TRAVIS_BUILD_DIR, "docker", "build")
DOCKER_PLAYS_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "docker", "plays")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")
LOGGER = logging.getLogger(__name__)


def build_graph(git_dir, roles_dirs, aws_play_dirs, docker_play_dirs):
    """
    Builds a dependency graph that shows relationships between roles and playbooks.
    An edge [A, B], where A and B are roles, signifies that A depends on B. An edge
    [C, D], where C is a playbook and D is a role, signifies that C uses D.

    Input:
    git_dir: A path to the top-most directory in the local git repository tool is to be run in.
    roles_dirs: A list of relative paths to directories in which Ansible roles reside.
    aws_play_dirs: A list of relative paths to directories in which AWS Ansible playbooks reside.
    docker_play_dirs: A list of relative paths to directories in which Docker Ansible playbooks reside.

    """

    graph = nx.DiGraph()

    _map_roles_to_roles(graph, roles_dirs, git_dir, "dependencies", "role", "role")
    _map_plays_to_roles(graph, aws_play_dirs, git_dir, "roles", "aws_playbook", "role")
    _map_plays_to_roles(graph, docker_play_dirs, git_dir, "roles", "docker_playbook", "role")

    return graph

def _map_roles_to_roles(graph, dirs, git_dir, key, type_1, type_2):
    """
    Maps roles to the roles that they depend on.

    Input:
    graph: A networkx digraph that is used to map Ansible dependencies.
    dirs: A list of relative paths to directories in which Ansible roles reside.
    git_dir: A path to the top-most directory in the local git repository tool is to be run in.
    key: The key in a role yaml file in dirs that maps to relevant role data. In this case, key is
        "dependencies", because a role's dependent roles is of interest.
    type_1: Given edges A-B, the type of node A.
    type_2: Given edges A-B, the type of node B.
        Since this function maps roles to their dependent roles, both type_1 and type_2 are "role".
    """

    Node = namedtuple('Node', ['name', 'type'])

    # for each role directory
    for d in dirs:
        d = pathlib2.Path(git_dir, d)

        # for all files/sub-directories in directory
        for item in d.iterdir():

            # attempts to find meta/*.yml file in item directory tree
            roles = {f for f in item.glob("meta/*.yml")}

            # if a meta/*.yml file(s) exists for a role
            if roles:
                # for each role
                for role in roles:
                    yaml_file = _open_yaml_file(role)

                    # if not an empty yaml file and key in file
                    if yaml_file is not None and key in yaml_file:
                        # for each dependent role; yaml_file["dependencies"] returns list of
                        # dependent roles
                        for dependent in yaml_file[key]:
                            # get role name of each dependent role
                            name = _get_role_name(dependent)

                            # add node for type_1, typically role
                            node_1 = Node(item.name, type_1)

                            # add node for type_2, typically dependent role
                            node_2 = Node(name, type_2)

                            # add edge, typically dependent role - role
                            graph.add_edge(node_2, node_1)

def _map_plays_to_roles(graph, dirs, git_dir, key, type_1, type_2):
    """
    Maps plays to the roles they use.

    Input:
    graph: A networkx digraph that is used to map Ansible dependencies.
    dirs: A list of relative paths to directories in which Ansible playbooks reside.
    git_dir: A path to the top-most directory in the local git repository tool is to be run in.
    key: The key in a playbook yaml file in dirs that maps to relevant playbook data. In this case, key is
        "roles", because the roles used by a playbook is of interest.
    type_1: Given edges A-B, the type of node A.
    type_2: Given edges A-B, the type of node B.
        Since this function maps plays to the roles they use, both type_1 is a type of playbook and type_2 is "role".
    """

    Node = namedtuple('Node', ['name', 'type'])

    # for each play directory
    for d in dirs:
        d = pathlib2.Path(git_dir, d)

        # for all files/sub-directories in directory
        for item in d.iterdir():

            # if item is a file ending in .yml
            if item.match("*.yml"):
                # open .yml file for playbook
                yaml_file = _open_yaml_file(item)

                # if not an empty yaml file
                if yaml_file is not None:
                    # for each play in yaml file
                    for play in yaml_file:
                        # if specified key in yaml file (e.g. "roles")
                        if key in play:
                            # for each role
                            for role in play[key]:
                                # get role name
                                name = _get_role_name(role)

                                #add node for type_1, typically for playbook
                                node_1 = Node(item.stem, type_1)

                                # add node for type_2, typically for role
                                node_2 = Node(name, type_2)

                                 # add edge, typically role - playbook that uses it
                                graph.add_edge(node_2, node_1)

def _open_yaml_file(file_str):
    """
    Opens yaml file.

    Input:
    file_str: The path to yaml file to be opened.
    """

    with (file_str.open(mode='r')) as file:
        try:
            yaml_file = yaml.safe_load(file)
            return yaml_file
        except yaml.YAMLError as exc:
            LOGGER.error("error in configuration file: %s" % str(exc))
            sys.exit(1)


def change_set_to_roles(files, git_dir, roles_dirs, playbooks_dirs, graph):
    """
    Converts change set consisting of a number of files to the roles that they represent/contain.

    Input:
    files: A list of files modified by a commit range.
    git_dir: A path to the top-most directory in the local git repository tool is to be run in.
    roles_dirs: A list of relative paths to directories in which Ansible roles reside.
    playbook_dirs: A list of relative paths to directories in which Ansible playbooks reside.
    graph: A networkx digraph that is used to map Ansible dependencies.
    """

    # set of roles
    items = set()

    # for all directories containing roles
    for role_dir in roles_dirs:
        role_dir_path = pathlib2.Path(git_dir, role_dir)

        # get all files in the directories containing roles (i.e. all the roles in that directory)
        candidate_files = {f for f in role_dir_path.glob("**/*")}

        # for all the files in the change set
        for f in files:
            file_path = pathlib2.Path(git_dir, f)

            # if the change set file is in the set of role files
            if file_path in candidate_files:
                # get name of role and add it to set of roles of the change set
                items.add(_get_role_name_from_file(file_path))
    return items


def get_plays(files, git_dir, playbooks_dirs):
    """
    Determines which files in the change set are aws playbooks

    files: A list of files modified by a commit range.
    git_dir: A path to the top-most directory in the local git repository tool is to be run in.
    playbook_dirs: A list of relative paths to directories in which Ansible playbooks reside.

    """

    plays = set()

    # for all directories containing playbooks
    for play_dir in playbooks_dirs:
        play_dir_path = pathlib2.Path(git_dir, play_dir)

        # get all files in directory containing playbook that end with yml extension
        # (i.e. all playbooks in that directory)
        candidate_files = {f for f in play_dir_path.glob("*.yml")}

        # for all filse in the change set
        for f in files:
            file_path = pathlib2.Path(git_dir, f)

            # if the change set file is in the set of playbook files
            if file_path in candidate_files:
                plays.add(_get_playbook_name_from_file(file_path))

    return plays


def _get_playbook_name_from_file(path):
    """
    Gets name of playbook from the filepath, which is the last part of the filepath.

    Input:
    path: A path to the playbook
    """
    # get last part of filepath
    return path.stem


def _get_role_name_from_file(path):
    """
    Gets name of role from the filepath, which is the directory following occurence of the word "roles".

    Input:
    path: A path to the role
    """
    # get individual parts of a file path
    dirs = path.parts

    # name of role is the next part of the file path after "roles"
    return dirs[dirs.index("roles")+1]


def get_dependencies(roles, graph):
    """
    Determines all roles dependent on set of roles and returns set containing both.

    Input:
    roles: A set of roles.
    graph: A networkx digraph that is used to map Ansible dependencies.
    """

    items = set()

    for role in roles:
        # add the role itself
        items.add(role)

        # add all the roles that depend on the role
        dependents = nx.descendants(graph, (role, "role"))

        items |= {dependent.name for dependent in dependents}

    return items


def get_docker_plays(roles, graph):
    """Gets all docker plays that contain at least role in common with roles."""

    # dict to determine coverage of plays
    coverage = dict.fromkeys(roles, False)

    items = set()

    docker_plays = {node.name for node in graph.nodes() if node.type == "docker_playbook"}

    for play in docker_plays:
        # all roles that are used by play
        roles_nodes = nx.all_neighbors(graph, (play, "docker_playbook"))

        docker_roles = {role.name for role in roles_nodes}

        # compares roles and docker roles
        common_roles = roles & docker_roles

        # if their intersection is non-empty, add the docker role
        if common_roles:
            items.add(play)

            # each aws role that was in common is marked as being covered by a docker play
            for role in common_roles:
                coverage[role] = True

    # check coverage of roles
    for role in coverage:
        if not coverage[role]:
            LOGGER.warning("role '%s' is not covered." % role)

    return items


def filter_docker_plays(plays, repo_path):
    """Filters out docker plays that do not have a Dockerfile."""

    items = set()

    for play in plays:
        dockerfile = pathlib2.Path(DOCKER_PATH_ROOT, play, "Dockerfile")

        if dockerfile.exists():
            items.add(play)
        else:
            LOGGER.warning("covered playbook '%s' does not have Dockerfile." % play)

    return items


def _get_role_name(role):
    """
    Resolves a role name from either a simple declaration or a dictionary style declaration.

    A simple declaration would look like:
    - foo

    A dictionary style declaration would look like:
    - role: rbenv
      rbenv_user: "{{ forum_user }}"
      rbenv_dir: "{{ forum_app_dir }}"
      rbenv_ruby_version: "{{ FORUM_RUBY_VERSION }}"

    :param role:
    :return:
    """
    if isinstance(role, dict):
        return role['role']
    elif isinstance(role, six.string_types):
        return role
    else:
        LOGGER.warning("role %s could not be resolved to a role name." % role)
        return None


def _get_modified_dockerfiles(files, git_dir):
    """
    Return changed files under docker/build directory
    :param files:
    :param git_dir:
    :return:
    """
    items = set()
    candidate_files = {f for f in DOCKER_PATH_ROOT.glob("**/*")}
    for f in files:
        file_path = pathlib2.Path(git_dir, f)
        if file_path in candidate_files:
            play = items.add(_get_play_name(file_path))

            if play is not None:
                items.add(play)

    return items


def get_modified_dockerfiles_plays(files, git_dir):
    """
    Return changed files under docker/plays directory
    :param files:
    :param git_dir:
    :return:
    """
    items = set()
    candidate_files = {f for f in DOCKER_PLAYS_PATH.glob("*.yml")}
    for f in files:
        file_path = pathlib2.Path(git_dir, f)
        if file_path in candidate_files:
            items.add(_get_playbook_name_from_file(file_path))
    return items


def _get_play_name(path):

    """
    Gets name of play from the filepath, which is the token
    after either "docker/build" in the file path.

    Input:
    path: A path to the changed file under docker/build dir
    """

    # attempt to extract Docker image name from file path; splits the path of a file over
    # "docker/build/", because the first token after "docker/build/" is the image name
    suffix = (str(path)).split(str(os.path.join('docker', 'build', '')))

    # if file path contains "docker/build/"
    if len(suffix) > 1:
        # split suffix over separators to file path components separately
        suffix_parts = suffix[1].split(os.sep)
        # first token will be image name; <repo>/docker/build/<image>/...
        return suffix_parts[0]
    return None


def arg_parse():

    parser = argparse.ArgumentParser(description = 'Given a commit range, analyze Ansible dependencies between roles and playbooks '
    'and output a list of Docker plays affected by this commit range via these dependencies.')
    parser.add_argument('--verbose', help="set warnings to be displayed", action="store_true")

    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    # configure logging
    logging.basicConfig()

    if not args.verbose:
        logging.disable(logging.WARNING)

    # set of modified files in the commit range
    change_set = set()

    # read from standard in
    for line in sys.stdin:
        change_set.add(line.rstrip())

    # configuration file is expected to be in the following format:
    #
    # roles_paths:
    #       - <all paths relative to configuration repository that contain Ansible roles>
    # aws_plays_paths:
    #       - <all paths relative to configuration repository that contain aws Ansible playbooks>
    # docker_plays_paths:
    #       - <all paths relative to configuration repository that contain Docker Ansible playbooks>

    # read config file
    config = _open_yaml_file(CONFIG_FILE_PATH)

    # build graph
    graph = build_graph(TRAVIS_BUILD_DIR, config["roles_paths"], config["aws_plays_paths"], config["docker_plays_paths"])

    # gets any playbooks in the commit range
    plays = get_plays(change_set, TRAVIS_BUILD_DIR, config["aws_plays_paths"])

    # transforms list of roles and plays into list of original roles and the roles contained in the plays
    roles = change_set_to_roles(change_set, TRAVIS_BUILD_DIR, config["roles_paths"], config["aws_plays_paths"], graph)

    # expands roles set to include roles that are dependent on existing roles
    dependent_roles = get_dependencies(roles, graph)

    # determine which docker plays cover at least one role
    docker_plays = get_docker_plays(dependent_roles, graph)

    docker_plays = docker_plays | plays

    # filter out docker plays without a Dockerfile
    docker_plays = filter_docker_plays(docker_plays, TRAVIS_BUILD_DIR)

    # Add playbooks to the list whose docker file has been modified
    modified_docker_files = _get_modified_dockerfiles(change_set, TRAVIS_BUILD_DIR)

    # Add plays to the list which got changed in docker/plays directory
    docker_plays_dir = get_modified_dockerfiles_plays(change_set, TRAVIS_BUILD_DIR)

    all_plays = set(set(docker_plays) | set( modified_docker_files) | set(docker_plays_dir))

    print(" ".join(all_plays))
