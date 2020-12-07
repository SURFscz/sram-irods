#!/bin/bash

# ###############################################
# this script creates an RPM from source code
# and spec file
# ###############################################

# parsing arguments
ERR=""
HELP=""
DRY=""
IRODS_VERSION=""
PACKAGE=""
VERSION=""
SPEC_FILE=""
SOURCE_DIR="/build/"
RELEASE=1

while [ $# -gt 0 ]; do
  case "$1" in
      --help*)
          HELP="1"
          ;;
      --dry*)
          DRY="1"
          ;;
      --irods-version*)
          shift
          IRODS_VERSION=$1
          ;;
      --package*)
          shift
          PACKAGE=$1
          ;;
      --version*)
          shift
          VERSION=$1
          ;;
      --release*)
          shift
          RELEASE=$1
          ;;
     --spec-file*)
          shift
          SPEC_FILE=$1
          ;;
      --source-dir*)
          shift
          SOURCE_DIR=$1
          ;;
      *)
          ERR="invalid argument: $1"
          break
  esac
  shift
done

if [[ -z "$VERSION" ]]
then
    ERR=$ERR"--version required\n\n"
else
    VERSION=$( echo $VERSION | sed 's/^v//' )
fi

if [[ ! "$VERSION" =~ ^[0-9]+(\.[0-9]+(\.[0-9]+)?)? ]]
then
    ERR=$ERR"invalid version: $VERSION\n"
    ERR=$ERR"exepected: <number> or <mayor.minor.patch>\n\n"
fi

if [[ -z "$IRODS_VERSION" ]]
then
    IRODS_VERSION=$( python3 <(cat << EOF
import json
with open("/var/lib/irods/VERSION.json") as fp:
     print(json.load(fp).get("irods_version"))
EOF
                              ))
fi

if [[ ! "$IRODS_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]
then
    ERR=$ERR"invalid irods version $IRODS_VERSION\n\n"
fi

if [[ -z "$PACKAGE" ]]
then
    ERR=$ERR"--package required\n\n"
fi

if [[ -z "$IRODS_VERSION" ]]
then
    ERR=$ERR"--irods-version required\n\n"
fi

if [[ -z "$SPEC_FILE" ]]
then
    ERR=$ERR"--spec-file required\n\n"
fi

if [ ! -z "$ERR" ]
then
    echo -e $ERR
fi

if [ ! -z "$HELP" ] || [ ! -z "$ERR" ]
then
    cat <<EOF
build_rpm.sh
usage: build_rpm.sh [OPTIONS]

OPTIONS:
        --help
        --dry
        --spec-file         SPEC_FILE (required)
        --package           NAME_OF_THE_PACKAGE (required)
        --version           VERSION (required)
                            Either build number of version string
        --irods-version     VERSION (optional)
                            if not set, read from /var/lib/irods/VERSION.json
        --source-dir        (optional, default /build

EOF
    if [ ! -z "$ERR" ]
    then
        exit 1
    else
        exit 0
    fi
fi

PSOURCE_DIR="^"$( echo $SOURCE_DIR | sed 's|^/||' )
if [ -z "$DRY" ]
then
    set -x
    tar --transform 's|'$PSOURCE_DIR'|'${PACKAGE}'-'${VERSION}/'|' -cvzf /home/rpmbuild/rpmbuild/SOURCES/${PACKAGE}-${VERSION}.tar.gz $SOURCE_DIR
    rpmbuild -bb --define "packagename $PACKAGE" --define "version $VERSION" --define "irodsversion $IRODS_VERSION" --define "release $RELEASE" $SPEC_FILE
    set +x
else
    echo tar --transform \''s|'$PSOURCE_DIR'|'${PACKAGE}'-'${VERSION}/'|'\' -cvzf /home/rpmbuild/rpmbuild/SOURCES/${PACKAGE}-${VERSION}.tar.gz $SOURCE_DIR
    echo rpmbuild -bb --define \"packagename $PACKAGE\" --define \"version $VERSION\" --define \"irodsversion $IRODS_VERSION\" --define \"release $RELEASE\" $SPEC_FILE
fi
