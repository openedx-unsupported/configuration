#!/bin/bash
# A very simple check to see if the json files in the project at least compile.
# If they do not, a cryptic message that might be helpful is produced.


# Save current directory so we can come back; change to repo root
STARTED_FROM=`pwd`
cd $(git rev-parse --show-toplevel)

# Do very basic syntax check of every json file to make sure it's valid format
for file in `find . -iname '*.json'`; do 
    cat $file | python -m json.tool 1>/dev/null 2>json_complaint.err; 
    retval=$?
    if [ $retval != 0 ]; then
        echo "JSON errors in $file"
        cat json_complaint.err
        rm -f json_complaint.err
        cd $STARTED_FROM
        exit $retval;
    fi
done

# Everything went ok!
rm -f json_complaint.err
cd $STARTED_FROM
exit 0
