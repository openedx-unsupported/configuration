#taken and modifid from lms/djangoapps/instructor_task/tasks_helper.py
#
# This is a quick and dirty hack to generate a course's grade report
#	without using Xqueue. 
#
# If we want to make this prettier in the future, we can set it up
#	as an admin.py command.
#
# Usage:
#	sudo su edxapp -s /bin/bash
#	source /edx/app/edxapp/edxapp_env
#	/edx/app/edxapp/edx-platform manage.py lms --settings=docker shell
#
#      >> execfile('/location/to/generateGradeReport.py')
#      >> upload_grades_csv('org/course_num/course_run')
#
# After that, grades should be downloaded to /tmp/edx-s3/ or 
#	uploaded to s3 based on django.conf.settings
#

#import everything just because
import json
from datetime import datetime
from time import time
import unicodecsv

from celery import Task, current_task
from celery.utils.log import get_task_logger
from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.files.storage import DefaultStorage
from django.db import transaction, reset_queries
import dogstats_wrapper as dog_stats_api
from pytz import UTC

from track.views import task_track
from util.file import course_filename_prefix_generator, UniversalNewlineIterator
from xmodule.modulestore.django import modulestore
from xmodule.split_test_module import get_split_user_partitions

from courseware.courses import get_course_by_id
from courseware.grades import iterate_grades_for
from courseware.models import StudentModule
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor_internal
from instructor_analytics.basic import enrolled_students_features
from instructor_analytics.csvs import format_dictlist
from instructor_task.models import ReportStore, InstructorTask, PROGRESS
from lms.djangoapps.lms_xblock.runtime import LmsPartitionService
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from student.models import CourseEnrollment

#turn course string into id
from opaque_keys.edx.locations import SlashSeparatedCourseKey

def upload_grades_csv(course_id_str):

    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_str)
    action_name = 'action_name' #not important

    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    enrolled_students = CourseEnrollment.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    course = get_course_by_id(course_id)
    cohorts_header = ['Cohort Name'] if course.is_cohorted else []

    experiment_partitions = get_split_user_partitions(course.user_partitions)
    group_configs_header = [u'Experiment Group ({})'.format(partition.name) for partition in experiment_partitions]

    # Loop over all our students and build our CSV lists in memory
    header = None
    rows = []
    err_rows = [["id", "username", "error_msg"]]
    current_step = {'step': 'Calculating Grades'}
    for student, gradeset, err_msg in iterate_grades_for(course_id, enrolled_students):
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        if gradeset:
            # We were able to successfully grade this student for this course.
            task_progress.succeeded += 1
            if not header:
                header = [section['label'] for section in gradeset[u'section_breakdown']]
                rows.append(
                    ["id", "email", "username", "grade"] + header + cohorts_header + group_configs_header
                )

            percents = {
                section['label']: section.get('percent', 0.0)
                for section in gradeset[u'section_breakdown']
                if 'label' in section
            }

            cohorts_group_name = []
            if course.is_cohorted:
                group = get_cohort(student, course_id, assign=False)
                cohorts_group_name.append(group.name if group else '')

            group_configs_group_names = []
            for partition in experiment_partitions:
                group = LmsPartitionService(student, course_id).get_group(partition, assign=False)
                group_configs_group_names.append(group.name if group else '')

            # Not everybody has the same gradable items. If the item is not
            # found in the user's gradeset, just assume it's a 0. The aggregated
            # grades for their sections and overall course will be calculated
            # without regard for the item they didn't have access to, so it's
            # possible for a student to have a 0.0 show up in their row but
            # still have 100% for the course.
            row_percents = [percents.get(label, 0.0) for label in header]
            rows.append(
                [student.id, student.email, student.username, gradeset['percent']] +
                row_percents + cohorts_group_name + group_configs_group_names
            )
        else:
            # An empty gradeset means we failed to grade a student.
            task_progress.failed += 1
            err_rows.append([student.id, student.username, err_msg])

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'grade_report', course_id, start_date)

    # If there are any error rows (don't count the header), write them out as well
    if len(err_rows) > 1:
        upload_csv_to_report_store(err_rows, 'grade_report_err', course_id, start_date)

    # One last update before we close out...
    return task_progress.update_task_state(extra_meta=current_step)

class TaskProgress(object):
    """
    Encapsulates the current task's progress by keeping track of
    'attempted', 'succeeded', 'skipped', 'failed', 'total',
    'action_name', and 'duration_ms' values.
    """
    def __init__(self, action_name, total, start_time):
        self.action_name = action_name
        self.total = total
        self.start_time = start_time
        self.attempted = 0
        self.succeeded = 0
        self.skipped = 0
        self.failed = 0

    def update_task_state(self, extra_meta=None):
        """
        Update the current celery task's state to the progress state
        specified by the current object.  Returns the progress
        dictionary for use by `run_main_task` and
        `BaseInstructorTask.on_success`.

        Arguments:
            extra_meta (dict): Extra metadata to pass to `update_state`

        Returns:
            dict: The current task's progress dict
        """
        progress_dict = {
            'action_name': self.action_name,
            'attempted': self.attempted,
            'succeeded': self.succeeded,
            'skipped': self.skipped,
            'failed': self.failed,
            'total': self.total,
            'duration_ms': int((time() - self.start_time) * 1000),
        }
        if extra_meta is not None:
            progress_dict.update(extra_meta)
        #_get_current_task().update_state(state=PROGRESS, meta=progress_dict)
        return progress_dict

def upload_csv_to_report_store(rows, csv_name, course_id, timestamp):
    """
    Upload data as a CSV using ReportStore.

    Arguments:
        rows: CSV data in the following format (first column may be a
            header):
            [
                [row1_colum1, row1_colum2, ...],
                ...
            ]
        csv_name: Name of the resulting CSV
        course_id: ID of the course
    """
    report_store = ReportStore.from_config()
    report_store.store_rows(
        course_id,
        u"{course_prefix}_{csv_name}_{timestamp_str}.csv".format(
            course_prefix=course_filename_prefix_generator(course_id),
            csv_name=csv_name,
            timestamp_str=timestamp.strftime("%Y-%m-%d-%H%M")
        ),
        rows
    )

