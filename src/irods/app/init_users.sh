#!/bin/bash
set -e
set -x
_MARA_PASSWORD=${MARA_PASSWORD:-mara}
_AYUB_PASSWORD=${AYUB_PASSWORD:-ayub}

for user in mara ayub
do
    if [ $( iadmin lu | grep -c '^'$user'#' ) == "0" ]
    then
        pvar="_"$( echo $user | sed 's/./\U&/g' )"_PASSWORD"
        iadmin mkuser $user rodsuser
        iadmin moduser $user password ${!pvar}
    fi
done

