import os
from django.contrib.auth.models import User

try:
    user = User.objects.get(username=os.environ.get('AUTH_USERNAME'))
except User.DoesNotExist:
    user = User.objects.create_user(username=os.environ.get('AUTH_USERNAME', ''),
                                    email='{}@skills.network'.format(os.environ.get('AUTH_USERNAME', '')),
                                    password=os.environ.get('AUTH_PASSWORD', ''))
except:
    quit()

user.is_superuser = True
user.is_staff = True
user.is_active = True
user.save()
quit()
