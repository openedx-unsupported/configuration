import time
from fabric.api import execute, local, task, runs_once
from fabric.utils import fastprint
from fabric.colors import blue
from ssh_tunnel import setup_tunnel

# These imports are to give aliases for these tasks
from hosts import by_name as name
from hosts import by_tags as tag
from hosts import by_tags as tags
from hosts import exemplar_from_tags as exemplar
from git import default_deploy as deploy
