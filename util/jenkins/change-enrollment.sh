cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -a"
manage="/edx/bin/python.edxapp /edx/bin/manage.edxapp lms change_enrollment --settings=aws"
noop_switch=""

if [ "$noop" = true ]; then
  noop_switch="--noop"  
fi

$ansible "$manage $noop_switch --course $course --user $name --to $to --from $from"
