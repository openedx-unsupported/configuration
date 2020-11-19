# TODO: when upgrading to Juniper, the import will change to:
# from lms.djangoapps.grades.models import PersistentGradesEnabled Flag
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag

flag = PersistentGradesEnabledFlag.objects.first()

if flag is None or not flag.enabled:
    PersistentGradesEnabledFlag.objects.create(enabled=True, enabled_for_all_courses=True)
else:
    flag.enabled=True
    flag.enabled_for_all_courses=True
    flag.save()

quit()
