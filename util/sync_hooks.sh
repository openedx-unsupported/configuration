#!/bin/bash
# A small utility to symlink the files from git-hooks/ with filenames ending
# like .in into the directory .git/hooks/
#
# It's intended this be run once near the start of a project by hand, and then
# subsequently a hook that it installs keeps it running at project checkouts.


# Save current directory so we can come back; change to repo root
STARTED_FROM=`pwd`
cd $(git rev-parse --show-toplevel)

# Sync git-hooks directory entries into .git/hooks/
for file in git-hooks/*.in; do
    filepart=`basename $file .in`
    if [ -e .git/hooks/$filepart -a ! -L .git/hooks/$filepart ]; then
        echo ".git/hooks/$filepart not link-managed; bailing..."
        echo "please examine your .git/hooks/ directory and repair inconsistencies manually"
        cd $STARTED_FROM
        exit 1
    else
        ln -v -s -f `pwd`/$file .git/hooks/$filepart
    fi
done

# Ok, everything went well; restore previous context
cd $STARTED_FROM
exit 0
