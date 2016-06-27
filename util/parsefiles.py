import os
import pathlib2
import logging
import yaml
import sys
import networkx as nx
from collections import namedtuple

class FileParser:

    def __init__(self):
        self._load_repo_path()

    def _load_repo_path(self):
        """Loads the path for the configuration repository from TRAVIS_BUILD_DIR environment variable."""

        if os.environ.get("TRAVIS_BUILD_DIR"):
            self.repo_path = os.environ.get("TRAVIS_BUILD_DIR")
        else:
            raise EnvironmentError("TRAVIS_BUILD_DIR environment variable is not set.")

    def build_graph(self, git_dir, roles_dirs, aws_play_dirs, docker_play_dirs):

        """
        Builds a dependency graph that shows relationships between roles and playbooks.
        An edge [A, B], where A and B are roles, signifies that A depends on B. An edge
        [C, D], where C is a playbook and D is a role, signifies that C uses D.
        """

        graph = nx.DiGraph()

        self._map_roles_to_roles(graph, roles_dirs, git_dir, "dependencies", "role", "role")
        self._map_plays_to_roles(graph, aws_play_dirs, git_dir, "roles", "aws_playbook", "role")
        self._map_plays_to_roles(graph, docker_play_dirs, git_dir, "roles", "docker_playbook", "role")

        return graph

    def _map_roles_to_roles(self, graph, dirs, git_dir, key, type_1, type_2):
        """Maps roles to the roles that they depend on."""

        Node = namedtuple('Node', ['name', 'type'])

        # for each role directory
        for d in dirs:
            d = pathlib2.Path(git_dir, d)

            if d.is_dir():
                # for all files/sub-directories in directory
                for directory in d.iterdir():

                    # attempts to find meta/*.yml file in directory
                    role = [file for file in directory.glob("meta/*.yml")]

                    # if role exists
                    if role:
                        with (open(str(role[0]), "r")) as file:
                            yaml_file = yaml.load(file)

                        # if a yaml file and key in file
                        if yaml_file is not None and key in yaml_file:
                            # for each dependent role
                            for dependent in yaml_file[key]:
                                # get role name
                                name = self._get_role_name(dependent)

                                # add node for role
                                node_1 = Node(directory.name, type_1)
                                # add node for dependent role
                                node_2 = Node(name, type_2)
                                # add edge role - dependent role
                                graph.add_edge(node_1, node_2)

    def _map_plays_to_roles(self, graph, dirs, git_dir, key, type_1, type_2):
        """Maps plays to the roles they use."""

        Node = namedtuple('Node', ['name', 'type'])

        # for each play directory
        for d in dirs:
            d = pathlib2.Path(git_dir, d)

            if d.is_dir():
                # for all files/sub-directories in directory
                for directory in d.iterdir():
                    # if a yaml file
                    if directory.is_file() and directory.suffix == ".yml":
                        with (open(str(directory), "r")) as file:
                            yaml_file = yaml.load(file)

                        if yaml_file is not None:
                            # for each play in yaml file
                            for play in yaml_file:
                                # if specified key in yaml file (e.g. "roles")
                                if key in play:
                                    # for each role
                                    for role in play[key]:
                                        # get role name
                                        name = self._get_role_name(role)

                                        # add node for playbook
                                        node_1 = Node(directory.stem, type_1)
                                        # add node for role
                                        node_2 = Node(name, type_2)
                                        # add edge playbook - role
                                        graph.add_edge(node_1, node_2)

    def change_set_to_roles(self, files, git_dir, roles_dirs, playbooks_dirs, graph):
        """Converts change set consisting of a number of files to the roles that they represent."""

        # set of roles
        items = set()

        # for all directories containing roles
        for role_dir in roles_dirs:
            role_dir_path = pathlib2.Path(git_dir, role_dir)

            # all files in role directory
            candidate_files = [file for file in role_dir_path.glob("**/*")]

            for file in files:
                file_path = pathlib2.Path(git_dir, file)

                if file_path in candidate_files:
                    name = self.get_resource_name(file_path, "roles")
                    items.add(name)

        # for all directories containing playbooks
        for play_dir in playbooks_dirs:
            play_dir_path = pathlib2.Path(git_dir, play_dir)

            # all files in role directory that end with yml extension
            candidate_files = [file for file in play_dir_path.glob("*.yml")]

            for file in files:
                file_path = pathlib2.Path(git_dir, file)

                if file_path in candidate_files:
                    name = self.get_resource_name(file_path, play_dir_path.name)

                    # gets first level of children of playbook in graph, which represents
                    # roles the playbook uses
                    descendants = nx.all_neighbors(graph, (file_path.stem, "aws_playbook"))

                    items |= {desc.name for desc in descendants}
        return items

    def get_resource_name(self, path, kind):
        """Gets name of resource from the filepath, which is the directory following occurence of kind."""

        dirs = path.parts
        index = dirs.index(kind)
        name = dirs[index+1]
        return name

    def get_dependencies(self, roles, graph):
        """Determines all roles dependent on set of roles and returns set containing both."""

        items = set()

        for role in roles:
            items.add(role)

            dependents = nx.descendants(graph, (role, "role"))

            names = {dep.name for dep in dependents}

            items |= names

        return items

    def get_docker_plays(self, roles, graph):
        """Gets all docker plays that contain at least role in common with roles."""

        # dict to determine coverage of plays
        coverage = dict.fromkeys(roles, False)

        items = set()

        docker_plays = [node.name for node in graph.nodes() if node.type == "docker_playbook"]

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

        self.check_coverage(coverage)

        return items

    def filter_docker_plays(self, plays, repo_path):
        """Filters out docker plays that do not have a Dockerfile."""

        items = set()
        logger = logging.getLogger(__name__)

        for play in plays:
            dockerfile = pathlib2.Path(self.repo_path, "docker", "build", play, "Dockerfile")

            if dockerfile.exists():
                items.add(play)
            else:
                logger.warning(" covered playbook '%s' does not have Dockerfile." % play)

        return items

    def check_coverage(self, coverage):
        """Checks which aws roles are not covered by docker plays."""

        logging.basicConfig(level=logging.WARNING)
        logger = logging.getLogger(__name__)

        for role in coverage:
            if not coverage[role]:
                logger.warning(" role '%s' is not covered." % role)

    def _get_role_name(self, role):
            """
            Resolves a role name from either a simple declaration or a dictionary style declaration.

            A simple declaration would look like:
            - foo

            A dictionary style declaration would look like:
            - role: rbenv
              rbenv_user: "{{ forum_user }}"
              rbenv_dir: "{{ forum_app_dir }}"
              rbenv_ruby_version: "{{ forum_ruby_version }}"

            :param role:
            :return:
            """
            if isinstance(role, dict):
                return role['role']
            elif isinstance(role, basestring):
                return role
            return None

if __name__ == '__main__':
    parser = FileParser()

    change_set = set()

    # read from standard in
    for line in sys.stdin:
        change_set.add(line.rstrip())

    # read config file
    config_file_path = pathlib2.Path(parser.repo_path, "util", "parsefiles_config.yml")

    with config_file_path.open() as config_file:
            config = yaml.load(config_file)

    # build grpah
    graph = parser.build_graph(parser.repo_path, config["roles_paths"], config["aws_plays_paths"], config["docker_plays_paths"])

    # transforms list of roles and plays into list of original roles and the roles contained in the plays
    roles = parser.change_set_to_roles(change_set, parser.repo_path, config["roles_paths"], config["aws_plays_paths"], graph)

    # expands roles set to include roles that are dependent on existing roles
    dependent_roles = parser.get_dependencies(roles, graph)

    # determine which docker plays cover at least one role
    docker_plays = parser.get_docker_plays(dependent_roles, graph)

    # filter out docker plays without a Dockerfile
    docker_plays = parser.filter_docker_plays(docker_plays, parser.repo_path)

    print " ".join(str(play) for play in docker_plays)
