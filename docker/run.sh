#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. Run starts an interactive shell:
# $ ./run.sh -t latest -db /abs/host/my_data_base -v /abs/host/dir:/abs/container/dir

user=$USER
db_path=''
vtag="latest"
mount_option=""

usage() {
  echo "USAGE:"
  echo "  ./run.sh [OPTIONS]
    "

  echo "DESCRIPTION:"
  echo "  Run 'romiscanner:<vtag>' container with a mounted local (host) database.
    "

  echo "OPTIONS:"
  echo "  -t, --tag
    Docker image tag to use, default to '$vtag'.
    "
  echo "  -db, --database_path
    Path to the host database to mount inside docker container, requires '--user' if not defautl.
    "
  echo "  -v, --volume
    Volume mapping for docker, e.g. '/abs/host/dir:/abs/container/dir'. Multiple use is allowed.
  "

  echo "  -h, --help
    Output a usage message and exit.
    "
}

while [ "$1" != "" ]; do
  case $1 in
  -t | --tag)
    shift
    vtag=$1
    ;;
  -u | --user)
    shift
    user=$1
    ;;
  -db | --database_path)
    shift
    db_path=$1
    ;;
  -v | --volume)
    shift
    if [ "$mount_option" == "" ]
    then
      mount_option="-v $1"
    else
      mount_option="$mount_option -v $1"  # append
    fi
    ;;
  -h | --help)
    usage
    exit
    ;;
  *)
    usage
    exit 1
    ;;
  esac
  shift
done

# Use 'host database path' & 'docker user' to create a bind mount:
if [ "$db_path" != "" ]
then
  mount_option="$mount_option -v $db_path:/home/$user/db"
fi

# Start in interactive mode:
docker run -it $mount_option --gpus all romiscanner:$vtag bash
