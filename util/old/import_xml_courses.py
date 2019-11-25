# Import XML Courses from git repos into the CMS.
# Run with sudo and make sure the user can clone
# the course repos.

# Output Has per course
#{
#    repo_url:
#    repo_name:
#    org:
#    course:
#    run:
#    disposition:
#    version:
#}

from __future__ import absolute_import
from __future__ import print_function
import argparse
from os.path import basename
import yaml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Import XML courses from git repos.")
    parser.add_argument("-c", "--courses-csv", required=True,
        help="A CSV of xml courses to import.")
    args = parser.parse_args()

    courses = open(args.courses_csv, 'r')

    all_course_data = []
    all_xml_mappings = {}
    for line in courses:
        cols = line.strip().split(',')
        slug = cols[0]
        author_format = cols[1]
        disposition = cols[2]
        repo_url = cols[4]
        version = cols[5]

        if author_format.lower() != 'xml' \
          or disposition.lower() == "don't import":
            continue

        # Checkout w/tilde
        org, course, run = slug.split("/")
        repo_name = "{}~{}".format(basename(repo_url).rstrip('.git'), run)

        course_info = {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "org": org,
            "course": course,
            "run": run,
            "disposition": disposition.lower(),
            "version": version,
        }
        all_course_data.append(course_info)

        if disposition.lower() == "on disk":
            all_xml_mappings[slug] = 'xml'

    edxapp_xml_courses = {
        "EDXAPP_XML_COURSES": all_course_data,
        "EDXAPP_XML_MAPPINGS": all_xml_mappings,
        "EDXAPP_XML_FROM_GIT": True
    }
    print(yaml.safe_dump(edxapp_xml_courses, default_flow_style=False))
