import yaml
import os
import pathlib2
import itertools
import sys

class ContainerBalancer:

    def __init__(self):
        self.load_repo_path()

    def load_repo_path(self):
        """Loads the path for the configuration repository from TRAVIS_BUILD_DIR environment variable."""

        if os.environ.get("TRAVIS_BUILD_DIR"):
            self.repo_path = os.environ.get("TRAVIS_BUILD_DIR")
        else:
            raise EnvironmentError("TRAVIS_BUILD_DIR environment variable is not set.")

    def pack_containers(self, containers):

        num_shards = 3

        config_file_path = pathlib2.Path(self.repo_path, "util", "parsefiles_config.yml")

        with config_file_path.open() as config_file:
                config = yaml.load(config_file)

        weights = config.get("weights")

        weights_list = [x.items() for x in weights]
        weights_list = list(itertools.chain.from_iterable(weights_list))

        used_containers = [x for x in weights_list if x[0] in containers]

        sorted_containers = sorted(used_containers, key = lambda x: x[1], reverse=True) 

        shards = []

        for i in range(0, num_shards):
            shards.append({"containers": [], "sum": 0})

        for container in sorted_containers:
            # shard with minimum execution time
            shard = min(shards, key = lambda x: x["sum"])

            shard["containers"].append(container)
            shard["sum"] += container[1]

        return shards

if __name__ == '__main__':

    balancer = ContainerBalancer()

    containers = []

    for line in sys.stdin:
        line = line.strip()
        line = line.strip("[]")

        items = line.split()
        containers.extend(items)

    # containers = {"discovery":6, "go-agent": 3, "xqwatcher": 3, "analytics_api": 1, "edxapp": 28, 
                  # "insights": 4, "credentials":8, "forum": 7, "nginx":1, "xqueue":2}

    # containers = ["discovery", "go-agent", "xqwatcher", "analytics_api", "edxapp", "insights", "credentials", "forum", "nginx", "xqueue"]
    # containers = ["discovery", "go-agent", "xqwatcher", "analytics_api", "insights", "credentials", "forum", "nginx", "xqueue"]
    # [discovery go-agent xqwatcher analytics_api edxapp insights credentials forum nginx xqueue]


    shards = balancer.pack_containers(containers)

    for shard in shards:
        middle = " "

        conts = [x[0] for x in shard["containers"]]

        line = middle.join(conts)
        print line

    # for shard in shards:
    #         for container in shard["containers"]:
    #             print container[0],
    #         print ""

    # containers.sort(reverse=True)


 # a={"discovery":6, "go-agent": 3, "xqwatcher": 3, "analytics_api": 1, "edxapp": 28, "insights": 4, "credentials":8, "forum":"nginx":1, "xqueue":2, "trusty-common":5, "precise-common":4}