MINID=0
MAXID=1003426362
STEP=20000
MIGRATE_USER=migrate
PASSWORD='secret'
HOST='host'
 
 
for ((i=$MINID-1; i<=$MAXID; i+=$STEP)); do
echo -n "$i";
time mysql -u $MIGRATE_USER -p$PASSWORD -h $HOST wwc <<EOF
  DELETE FROM courseware_studentmodulehistory where id < $i
EOF
sleep 3;
done
