cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -m shell -a"
manage="cd /edx/app/edxapp/edx-platform && /edx/bin/python.edxapp /edx/bin/manage.edxapp lms change_enrollment --settings aws"

if [ "$noop" = true ]; then
  $ansible "$manage --noop --course $course --to $to --from $from"
else
  $ansible "$manage --course $course --to $to --from $from"
fi
