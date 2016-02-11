from xmodule.modulestore.django import modulestore
from django.contrib.auth.models import User
from instructor.utils import DummyRequest
from instructor.views.legacy import get_student_grade_summary_data

import csv 

from django.contrib.auth.models import User
random_user = User.objects.all()[0]

fp = open('/tmp/gradeOutputFull.csv','w')
writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
request = DummyRequest()
request.user = random_user

mongo_courses = modulestore().get_courses()

writer.writerow(['course_id','user_id','username','full_name','email','course_access_group','final_score'])
for course in mongo_courses:
#course_id = 'course-v1:Metalogix+EO301+2015'
#course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
#course = get_course_by_id(course_key)
    get_raw_scores = False
    datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
    for d in datatable['data']:
        user_id = d[0]
        user = User.objects.get(id=user_id)
        try:
		    course_access_group = user.courseaccessgroup_set.all()[0].name #assume there's at least one group and get it
        except:
            course_access_group = 'None'
        output_data = [course.id, d[0], d[1], d[2], d[3], course_access_group, d[len(d)-1]]
        encoded_row = [unicode(s).encode('utf-8') for s in output_data]
        #writer.writerow(output_data)
        writer.writerow(encoded_row)

fp.close()

