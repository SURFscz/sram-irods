#!/bin/bash

# wait for service
RETRIES=10
res=1
set +e
while [[ $res -ne  0 ]]
do
    curl icat.irods:1247
    res=$?
    if [ $res != 0 ];
    then
        RETRIES=$(( RETRIES - 1 ))
        if [ $RETRIES == 0 ]
        then
            echo "cannot connect to icat"
            cat /app/setup_irods.log
            exit 8
        fi
        echo "failed: try again ($RETRIES attempts)"
        sleep 10
    fi
done
set -e
