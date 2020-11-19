import os
from django.contrib.auth.models import User

try:
    user = User.objects.get(username=os.environ.get('BDU_PORTAL_MANAGER_USERNAME'))
except User.DoesNotExist: 
    user = User.objects.create_user(username=os.environ.get('BDU_PORTAL_MANAGER_USERNAME', ''), 
                                    email=os.environ.get('BDU_PORTAL_MANAGER_EMAIL', ''), 
                                    password=os.environ.get('BDU_PORTAL_MANAGER_PASSWORD', ''))
except:
    quit()

user.is_superuser = True
user.is_staff = True
user.is_active = True
user.save()
quit()
