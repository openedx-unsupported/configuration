#!/usr/bin/env python
import os
import subprocess
import re
import json
import glob

ROOT_DIR = '/opt/wwc'
VERSION_FILE = '/opt/wwc/versions.html'
VERSION_JSON = '/opt/wwc/versions.json'
GLOB_DIRS = [
              os.path.join(ROOT_DIR, '*/.git'),
              os.path.join(ROOT_DIR, '*/*/.git'),
              os.path.join(ROOT_DIR, 'data/*/.git'),
            ]


TEMPLATE = """
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title></title>
    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js"></script>

    <style>
      body {{
         font-size: 2em;
         color: #000;
         font-family: monospace;
      }}
    </style>

  </head>
<body>
<ul>
  {BODY}
</ul>
</body>
<script type="text/javascript">
  $(".collapse").click(function () {{
        $(this).parent().children().toggle();
        $(this).toggle();

        }});
  $(document).ready(function() {{
        $('.collapse').parent().children().toggle();
        $('.collapse').toggle();
  }});
</script>
</html>
"""


def main():
    assert os.path.isdir(ROOT_DIR)
    # using glob with fixed depths is much
    # faster than os.walk for finding all .git repos
    git_dirs = [git_dir for glob_dir in GLOB_DIRS
                for git_dir in glob.glob(glob_dir)]
    git_dirs = filter(lambda f: os.path.isdir(f), git_dirs)

    version_info = ""
    versions = {}

    for git_dir in git_dirs:
        repo_dir = git_dir.replace('/.git', '')
        repo_dir_basename = os.path.basename(repo_dir)

        # get the revision of the repo
        p = subprocess.Popen(['/usr/bin/git', 'rev-parse', 'HEAD'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=git_dir)
        rev_output, rev_err = p.communicate()
        revision = rev_output.splitlines()[0][:8]

        # dictionary that will be written out as JSON
        versions[repo_dir_basename] = revision

        # use reflogs for the repo history
        p = subprocess.Popen(
          ['/usr/bin/git', 'log', '-g', '--abbrev-commit', '--pretty=oneline'],
           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_dir)

        reflog_output, reflog_err = p.communicate()

        # ignore lines that do not have 'HEAD'
        reflog_lines = filter(lambda x: x.find('HEAD') >= 0,
                                            reflog_output.splitlines())

        # get the repo name, `git remote -v` seems like the fastest option
        p = subprocess.Popen(['/usr/bin/git', 'remote', '-v'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=git_dir)
        remote_output, remote_err = p.communicate()
        repo_url = None
        for line in remote_output.splitlines():
            if ' (fetch)' in line:
                repo_url = re.search(
                        '(git@|git://)(.*) \(fetch\)', line).group(2).replace(
                                                                ':', '/')
                break
        if not repo_url:
            raise Exception("Unable to parse repo name")

        version_info += """
          <li> <span class="collapse"> <a href="http://{0}">{1}</a> - {2}
                [ click for history (most recent last) ]</span>
          <ul>""".format(repo_url, repo_dir_basename, revision)

        ref_prev = None
        for line in reflog_lines[:0:-1]:
            ref = line.split()[0]
            version_info += """
              <li><span class="collapse">{ref} -
              <a href="http://{repo}/compare/{ref}...{revision}">[diff current]</a>
              """.format(ref=ref, repo=repo_url, revision=revision)

            if ref_prev:
                version_info += """
                <a href="http://{repo}/compare/{ref_prev}...{ref}">[diff previous]</a>
                """.format(repo=repo_url, ref=ref, ref_prev=ref_prev)
            version_info += "</span></li>"
            ref_prev = ref
        version_info += """
          </ul></li>"""

    with open(VERSION_FILE, 'w') as f:
        f.write(TEMPLATE.format(BODY=version_info))
    with open(VERSION_JSON, 'w') as f:
        f.write(json.dumps(versions, sort_keys=True, indent=4,
                        separators=(',', ': ')))

if __name__ == '__main__':
    main()
