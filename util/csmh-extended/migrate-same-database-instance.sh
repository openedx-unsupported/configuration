#!/bin/bash
MINID=0
MAXID=1003426362
STEP=10000
MIGRATE_USER=migrate
PASSWORD='password'
HOST='localhost'
 
 
for ((i=0; i<=$MAXID; i+=$STEP)); do
echo -n "$i";
mysql -u $MIGRATE_USER -p$PASSWORD -h $HOST edxapp <<EOF
INSERT INTO edxapp_csmh.coursewarehistoryextended_studentmodulehistoryextended (id, version, created, state, grade, max_grade, student_module_id)
  SELECT id, version, created, state, grade, max_grade, student_module_id
  FROM edxapp.courseware_studentmodulehistory
  WHERE id BETWEEN $i AND $(($i+$STEP-1));
EOF
echo '.';
sleep 2
done
