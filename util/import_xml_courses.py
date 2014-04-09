# Import XML Courses from git repos into the CMS.
# Run with sudo and make sure the user can clone
# the course repos.

import argparse
import logging
import subprocess
from os.path import basename, exists, join
from os import chdir
from getpass import getuser

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Import XML courses from git repos.")
    parser.add_argument("-c", "--courses-csv", required=True,
        help="A CSV of xml courses to import.")
    parser.add_argument("-d", "--data-dir", required=True,
        help="The location to checkout the repos for import.")
    args = parser.parse_args()

    courses = open(args.courses_csv, 'r')

    # Go to the platform dir.
    # Need this for dealer to work.
    chdir("/edx/app/edxapp/edx-platform")

    for line in courses:
        cols = line.strip().split(',')
        slug = cols[0]
        author_format = cols[1]
        disposition = cols[2]
        repo_url = cols[4]

        if author_format.lower() != 'xml' \
          or disposition.lower() == "don't import" \
          or disposition.lower() == 'on disk':
            continue

        logging.debug("{}: {}".format(slug, repo_url))
        org, course, run = slug.split("/")
        repo_name = "{}".format(basename(repo_url).rstrip('.git'), run)

        # Clone course into data dir.
        repo_location = join(args.data_dir, repo_name)
        if not exists(repo_location):
            cmd = "git clone {} {}".format(repo_url, repo_location)
            subprocess.check_call(cmd,shell=True)
            chown_cmd = "chown -R www-data:edxapp {}".format(repo_location)
            subprocess.check_call(chown_cmd, shell=True)

        # Update course.xml
        course_xml_path = join(repo_location, "course.xml")
        xml_content = '<course org="{}" course="{}" url_name="{}"/>'
        f = open(course_xml_path, 'w')
        f.write(xml_content.format(org, course, run))
        f.close()

        # Import the course
        if disposition.lower() == "import":
            # Import into cms
            cmd = "sudo -E -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-platform/manage.py cms --settings=aws import {} {}".format(args.data_dir, repo_name)
            logging.debug("Running cmd:: {}".format(cmd))
            subprocess.check_call(cmd, shell=True)
        elif disposition.lower() == "no static import":
            # Update courses.xml
            # Import with --nostatic
            cmd = "sudo -E -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-platform/manage.py cms --settings=aws import --nostatic {} {}".format(args.data_dir, repo_name)
            logging.debug("Running cmd:: {}".format(cmd))
            subprocess.check_call(cmd, shell=True)

