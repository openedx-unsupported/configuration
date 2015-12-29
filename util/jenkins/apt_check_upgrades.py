#!/usr/bin/env python
import apt
import argparse

def parse_args():
  description = "Print machine-readable output detailing available upgrades for specified packages"
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('-y', '--yaml', action='store_true', 
    help="change output format to YAML (NB: requires pyyaml) [default: JSON]")
  parser.add_argument('-a', '--all', action='store_true', help="check all packages for upgrade")
  parser.add_argument('packages', nargs='*', help="packages to check for upgrade")
  
  args = parser.parse_args()
  
  if args.yaml:
    import yaml
    global yaml
  else:
    import json
    global json
  
  return args


def check_upgrade(pkg):
  if pkg.installed != pkg.candidate:
    return {
      'current_version': pkg.installed.version,
      'new_version': pkg.candidate.version,
      'summary': pkg.candidate.summary,
      'current_md5': pkg.installed.md5,
      'new_md5': pkg.candidate.md5,
      'homepage': pkg.candidate.homepage,
    }


def main(args):
  need_upgrade = {}
  cache = apt.Cache()
  
  if args.all:
    for pkg in cache:
      if pkg.is_installed:
        result = check_upgrade(pkg)
        if result:
          need_upgrade[pkg.name] = result
  else:
    for pkg_name in args.packages:
      if pkg_name not in cache:
        raise Exception('no package named "{}" exists in the cache!'.format(pkg_name))
      result = check_upgrade(cache[pkg_name])
      if result:
        need_upgrade[pkg_name] = result

  if need_upgrade:
    if args.yaml:
      output = yaml.dump(need_upgrade, default_flow_style=False)
    else:
      output = json.dumps(need_upgrade)
    print output



if __name__ == '__main__':
  main(parse_args())
