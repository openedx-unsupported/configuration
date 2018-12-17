import click
import yaml
import json

@click.command()
@click.option('--files', '-m', multiple=True)
def check_for_yaml_key_collisions(files):
    values_for_keys = {}
    for file_path in files:
        content = None
        if ".yml" in file_path or ".yaml" in file_path:
            stream = file(file_path, 'r')
            content = yaml.load(stream)
        elif ".json" in file_path:
            with open(file_path, "r") as read_file:
                content = json.load(read_file)
        for key, value in content.iteritems():
            if key not in values_for_keys:
                values_for_keys[key] = []
            values_for_keys[key].append(value)

    collisions = {}

    for key,value in values_for_keys.iteritems():
        if len(value) > 1:
            collisions[key] = value


    if len(collisions.keys()) > 0:
        print(str.format("Found key collisions: {}", len(collisions)))
        for key,value in collisions.iteritems():
            print(str.format("{} {}", key, value))
        exit(1)
    else:
        print("No collisions found")
        exit(0)

if __name__ == '__main__':
    check_for_yaml_key_collisions()