#!/bin/bash

RETRIES=10
_PG_HOST=${PG_HOST:-postgres}
_PG_USER=${PG_USER:-irods}
_PG_DATABASE=${PG_DATABASE:-ICAT}
_IRODS_DB_PASSWORD=${IRODS_DB_PASSWORD:-irods}

err=1
while [ $err != 0 ]
do
    echo "attempt to connect to database"
    PGPASSWORD=$_IRODS_DB_PASSWORD psql --user $_PG_USER --host=$_PG_HOST --command='\q' $_PG_DATABASE
    err=$?
    RETRIES=$(( RETRIES - 1 ))
    if [ $err != 0 ];
    then
        if [ $RETRIES == 0 ]
        then
            echo "cannot connect to database"
            exit 8
        fi
        echo "failed: try again ($attempts attempts)"
    fi
    sleep 5;
done


