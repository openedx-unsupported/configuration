# sample script for auto registering users into open edx via csv file
# tested on cypress and dogwood

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import translation

from student.forms import AccountCreationForm
from student.models import CourseEnrollment, create_comments_service_user
from student.views import _do_create_account, AccountValidationError
from track.management.tracked_command import TrackedCommand

import csv

##example testcsv.csv file:
#username,firstname,lastname,email,password,pi,oucu
#test.username,firstname,lastname,testemail@example.com,testpassword
#test.username2,firstname2,lastname2,testemail2@example.com,testpassword
#test.username,firstname,lastname,testemail@example.com,testpassword

#emails = ['tj.2test@appsembler.com' ]
with open('/tmp/testcsv.csv','rb') as csvfile: 
    csvreader = csv.reader(csvfile,delimiter=',')
    csvreader.next() #skip first row of labels
    for row in csvreader:
        try:
            username = row[0]
            name = row[1] + ' ' + row[2]
            email = row[3]
            password = row[4]
            if User.objects.filter(email=email):
                print 'user {} already exists; skipping'.format(email)
                continue
            form = AccountCreationForm(
                data={
                    'username': username,
                    'email': email,
                    'password': password,
                    'name': name,
                },
                tos_required=False
            )        
            # django.utils.translation.get_language() will be used to set the new
            # user's preferred language.  This line ensures that the result will
            # match this installation's default locale.  Otherwise, inside a
            # management command, it will always return "en-us".
            translation.activate(settings.LANGUAGE_CODE)
            try:
                user, _, reg = _do_create_account(form)
                reg.activate()
                reg.save()
                create_comments_service_user(user)
            except AccountValidationError as e:
                print e.message
                user = User.objects.get(email=email)
            translation.deactivate()
            print 'successfully created user for {}'.format(email)
        except Exception as e:
            print 'could not create user: {}'.format(username)
            print e
            continue


