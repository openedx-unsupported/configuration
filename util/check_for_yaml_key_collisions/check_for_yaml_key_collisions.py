import click
from yaml import load, dump

@click.command()
@click.option('--files', '-m', multiple=True)
def check_for_yaml_key_collisions(files):
    
    key_to_value_map = {}
    key_collisions = []
    for file_path in files:
        stream = file(file_path, 'r')
        content = load(stream)
        for key,value in content.iteritems():
            if key in key_to_value_map.keys():
                key_collisions.append(key)
            else:
                key_to_value_map[key] = value

    if len(key_collisions) > 0:
        print(str.format("Found key collisions: {}", len(key_collisions)))
        for key_collision in key_collisions:
            print(key_collision)
        exit(1)
    else:
        print("No collisions found")
        exit(0)

if __name__ == '__main__':
    check_for_yaml_key_collisions()