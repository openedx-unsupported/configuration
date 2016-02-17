
# instructions:
#   ---on open edx server
#       cd /edx/app/edxapp/edx-platform
#       source ../edxapp_env
#       python manage.py lms --settings=aws_appsembler shell  
#   
#       inside the django shell, execute this script
#       
#  ---after script has executed
#  scp academy.metalogix.com:/tmp/gradeOutputFull.csv ./gradeOutputFull20160211.csv
#  
#
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

writer.writerow(['#course_id', 'course_name','user_id','username','full_name','email','location','city','country','course_access_group','registered','is_active','last_login','final_score'])
for course in mongo_courses:
#location, city, country; registered, is_active, last_login
#course_id = 'course-v1:Metalogix+EO301+2015'
#course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
#course = get_course_by_id(course_key)
    course_name = course.display_name
    get_raw_scores = False
    datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
    for d in datatable['data']:
        user_id = d[0]
        u = User.objects.get(id=user_id)
        cag = u.courseaccessgroup_set.all()
        if not cag:
            cag = ''
        else:
            cag = cag[0]
        try: 
            loc = u.profile.location
        except Exception:
            loc = ''
        try: 
            p = u.profile   
            city = str(p.city)
            country = str(p.country)
            full_name = str(p.name)
        except Exception: #profile doesn't exist or city isn't ascii
            city = ''
            country = ''
            full_name = ''
        # try:
        #     course_access_group = user.courseaccessgroup_set.all()[0].name #assume there's at least one group and get it
        #     p = user.profile
        # except:
        #     course_access_group = 'None'
        output_data = [course.id,
                       course_name,
                        str(u.id), 
                        u.username, 
                        full_name, 
                        u.email,
                        loc,
                        city,
                        country,
                        str(cag), 
                        str(u.date_joined),
                        u.is_active,
                        str(u.last_login),
                        d[len(d)-1]
                    ]
        encoded_row = [unicode(s).encode('utf-8') for s in output_data]
        #writer.writerow(output_data)
        writer.writerow(encoded_row)

fp.close()

