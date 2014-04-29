#!/bin/bash
# A very simple check to see if the json files in the project at least compile.
# If they do not, a cryptic message that might be helpful is produced.


# Save current directory so we can come back; change to repo root
pushd $(git rev-parse --show-toplevel) >/dev/null

# Do very basic syntax check of every json file to make sure it's valid format
for file in `find . -iname '*.json'`; do 
    errors=$(python -m json.tool "$file" 2>&1 1>/dev/null)
    retval=$?
    if [ $retval != 0 ]; then
        echo "JSON errors in $file"
        echo "$errors"
        popd >/dev/null
        exit $retval;
    fi
done

# Everything went ok!
popd >/dev/null
exit 0
