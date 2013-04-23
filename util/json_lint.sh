#!/bin/bash

# Do very basic syntax check of every json file to make sure it's valid format
for file in `find . -iname '*.json'`; do 
    cat $file | python -m json.tool 1>/dev/null 2>json_complaint.err; 
    retval=$?
    if [ $retval != 0 ]; then
        echo "JSON errors in $file"
        cat json_complaint.err
        rm -f json_complaint.err
        exit $retval;
    fi
done

# Everything went ok!
exit 0
