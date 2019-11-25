import click
import yaml

@click.command()
@click.option('--values', help='Path to a values.yaml file', required=True)
@click.option('--subcharts', help='Sub chart values to ignore', multiple=True)
def cli(values, subcharts):
    with open(values, 'r') as stream:
      parsed_dict = yaml.safe_load(stream)
      keys_from_yaml = collect_keys_from_yaml(parsed_dict, subcharts)
      col_width = 99
      print_header(col_width)
      for dot_format_key in keys_from_yaml:
        value = extract_default_using_dot_key(dot_format_key, parsed_dict)
        print_row(dot_format_key, value, col_width)
      print_bar(col_width)

def collect_keys_from_yaml(parsed_dict, subcharts):
  aggregate = []
  outp = get_keys("", parsed_dict)
  for entry in outp:
    first_part_of_key = entry.split(".")[0]

    if first_part_of_key not in subcharts or entry.endswith(".enabled"):
      aggregate.append(entry)
  return aggregate

def print_bar(col_width):
  p1 = int(col_width) * "=" 
  p2 = int(col_width) * "=" 
  p3 = int(col_width) * "=" 
  print(f"{p1}  {p2}  {p3}")

def print_header(col_width):
  word1 = "Parameter"
  num_spaces1  = col_width - len(word1)
  num_spaces1 = num_spaces1 + 1
  spaces1 = " " * num_spaces1

  word2 = "Description"
  num_spaces2  = col_width - len(word2)
  num_spaces2 = num_spaces2 + 1
  spaces2 = " " * num_spaces2

  word3 = "Default"
  num_spaces3  = col_width - len(word3)
  spaces3 = " " * num_spaces3

  print_bar(col_width)
  print(f"{word1}{spaces1} {word2}{spaces2} {word3}{spaces3}")
  print_bar(col_width)

def print_row(dot_format_key, value, col_width):
  space1 = (" " * (col_width - len(dot_format_key)))
  space2 = (" " * (col_width - len(dot_format_key)))
  space3 = " " * (len(dot_format_key) - 2)
  print(f"{dot_format_key}{space1}  TODO{space2}{space3}{value}")

def get_keys(prefix, inp):
  if isinstance(inp, dict):
    aggregate = []
    for child_key in inp.keys():
      child = inp[child_key]

      if prefix is not "":
        modified_prefix = prefix + "."
      else:
        modified_prefix = prefix

      if isinstance(child, dict):
            aggregate.append(get_keys(modified_prefix + child_key, child))
      else:
          aggregate.append(modified_prefix + child_key)
    return flatten(aggregate);

def extract_default_using_dot_key(dot_format_key, parsed_dict):
  key_parts = dot_format_key.split(".")
  result = parsed_dict
  for key_part in key_parts:
    result = result[key_part]
  return result
   
def flatten(target):
    if target == []:
        return target
    if isinstance(target[0], list):
        return flatten(target[0]) + flatten(target[1:])
    return target[:1] + flatten(target[1:]) 

if __name__ == '__main__':
    cli()