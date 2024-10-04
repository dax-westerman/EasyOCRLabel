#!/usr/bin/bash

for FILE in *.part*; do
    echo ''
    echo "Adding $FILE"
    git add -f "$FILE"
    git commit -m "$FILE"
    git push
    echo ''
    sleep 1
done
