# Import XML Courses from git repos into the CMS.
# Run with sudo and make sure the user can clone
# the course repos.

import argparse
import logging
import subprocess
from os.path import basename, exists, join
import os
import contextlib
from getpass import getuser

logging.basicConfig(level=logging.DEBUG)

@contextlib.contextmanager
def chdir(dirname=None):
  curdir = os.getcwd()
  try:
    if dirname is not None:
      os.chdir(dirname)
    yield
  finally:
    os.chdir(curdir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Import XML courses from git repos.")
    parser.add_argument("-c", "--courses-csv", required=True,
        help="A CSV of xml courses to import.")
    parser.add_argument("-d", "--var-dir", default="/edx/var/edxapp",
        help="The location of the edxapp var directory that hold the data and courstatic dirs.")
    args = parser.parse_args()

    courses = open(args.courses_csv, 'r')
    data_dir = join(args.var_dir, 'data')
    static_dir = join(args.var_dir, 'course_static')


    cwd = getcwd()
    platform_dir = "/edx/app/edxapp/edx-platform"

    for line in courses:
        cols = line.strip().split(',')
        slug = cols[0]
        author_format = cols[1]
        disposition = cols[2]
        repo_url = cols[4]

        if author_format.lower() != 'xml' \
          or disposition.lower() == "don't import":
            continue

        # Checkout w/tilde
        logging.debug("{}: {}".format(slug, repo_url))
        org, course, run = slug.split("/")
        repo_name = "{}~{}".format(basename(repo_url).rstrip('.git'), run)

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


        if disposition.lower() == "on disk":
            with chdir(args.static_dir):
                # Link static files to course_static dir
                static_location = join(repo_location, 'static')
                cmd = "ln -sf {} {}".format(static_location, repo_name)
                logging.debug("Running cmd: {}".format(cmd))
                subprocess.check_call(cmd, shell=True)
        elif disposition.lower() == 'no static import':
            # Go to the platform dir.
            # Need this for dealer to work.
            with chdir(platform_dir):
                # Import w/nostatic flag
                cmd = "sudo -E -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-platform/manage.py cms --settings=aws import --nostatic {} {}".format(args.data_dir, repo_name)
                logging.debug("Running cmd: {}".format(cmd))
                subprocess.check_call(cmd, shell=True)

            with chdir(args.static_dir):
                # Link static files to course_static dir.
                static_location = join(repo_location, 'static')
                cmd = "ln -sf {} {}".format(static_location, repo_name)
                logging.debug("Running cmd: {}".format(cmd))
                subprocess.check_call(cmd, shell=True)

        elif disposition.lower() == 'import':
            # Go to the platform dir.
            # Need this for dealer to work.
            with chdir(platform_dir):
                # Import
                cmd = "sudo -E -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-platform/manage.py cms --settings=aws import {} {}".format(args.data_dir, repo_name)
                logging.debug("Running cmd: {}".format(cmd))
                subprocess.check_call(cmd, shell=True)

            # Remove from disk.
            cmd = "sudo rm -rf {}".format(repo_location)
            logging.debug("Running cmd: {}".format(cmd))
            subprocess.check_call(cmd, shell=True)

    # Create the tar file of all xml courses
    cmd = "sudo tar cvzf static_course_content.tar.gz -C {} data course_static".format(args.var_dir)
    logging.debug("Running cmd: {}".format(cmd))
    subprocess.check_call(cmd, shell=True)

