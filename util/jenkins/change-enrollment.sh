cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -a"
manage="/edx/bin/python.edxapp /edx/bin/manage.edxapp lms change_enrollment --settings=aws"
noop=""

if [ "$noop" = true ]; then
  noop="--noop"  
fi

$ansible "$manage $noop --course $course --user $name --to $to --from $from"
