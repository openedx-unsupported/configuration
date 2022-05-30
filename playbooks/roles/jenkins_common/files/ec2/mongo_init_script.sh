# This confirms that mongo is running and is accessible on localhost
# It could expose internal network problems, in which case the worker should not be used
# Mongo seems to spend a bit of time starting.
i=0

while [ $i -lt 45 ]; do
    mongo --quiet --eval 'db.getMongo().getDBNames()' 2>/dev/null 1>&2
    if [ $? -eq 0 ]; then
        break
    else
        sleep 2
        i=$[$i+1]
    fi
done

mongo --quiet --eval 'db.getMongo().getDBNames()'
