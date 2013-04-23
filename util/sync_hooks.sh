#!/bin/bash

# Are we running from the git root?
GITHOOKSFOUND='false'
if [ -d git-hooks ]; then
    GITHOOKSFOUND='true';
fi
DOTGITHOOKSFOUND='false'
if [ -d .git -a -d .git/hooks ]; then
    DOTGITHOOKSFOUND='true';
fi

# Sync git-hooks directory entries into .git/hooks/
if [ 'true' = $GITHOOKSFOUND -a 'true' = $DOTGITHOOKSFOUND ]; then
    for file in git-hooks/*; do
        filepart=`echo $file | sed -e 's/git-hooks\/\(.*\)/\1/'`
        if [ -e .git/hooks/$filepart -a ! -L .git/hooks/$filepart ]; then
            echo ".git/hooks/$filepart not link-managed; bailing..."
            echo "please examine your .git/hooks/ directory and repair inconsistencies manually"
            exit 1
        else
            ln -v -s -b -f `pwd`/$file -t .git/hooks/
        fi
    done
else
    echo "Not in git repository root, cannot continue."
    exit 1
fi

# Ok, everything went well
exit 0
