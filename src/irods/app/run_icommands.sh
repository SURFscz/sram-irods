#!/bin/bash

if [ ! -z "$IRODS_ZONE" ]
then
    sed -i "s/tempZone/$IRODS_ZONE/g" /home/mara/.irods/irods_environment.json
    sed -i "s/tempZone/$IRODS_ZONE/g" /home/ayub/.irods/irods_environment.json
fi

sleep infinity
