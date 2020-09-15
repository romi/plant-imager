#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. Default run starts an interactive shell:
# $ ./run.sh


db_path=''
vtag="latest"
cmd=''

usage() {
  echo "USAGE:"
  echo "  ./run.sh [OPTIONS]
    "

  echo "DESCRIPTION:"
  echo "  Run 'roboticsmicrofarms/romiscan:<vtag>' container with a mounted local (host) database.
    "

  echo "OPTIONS:"
  echo "  -t, --tag
    Docker image tag to use, default to '$vtag'.
    "
  echo "  -p, --database_path
    Path to the host database to mount inside docker container, requires '--user' if not defautl.
    "

  echo "  -c, --cmd
    Defines the command to run at docker startup, by default start an interactive container with a bash shell.
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
  -p | --database_path)
    shift
    db_path=$1
    ;;
  -c | --cmd)
    shift
    cmd=$1
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
  mount_option="-v $db_path:/home/$user/db"
else
  mount_option=""
fi


if [ "$cmd" = "" ]
then
  # Start in interactive mode:
  docker run --runtime=nvidia --gpus all $mount_option \
    --env PYOPENCL_CTX='0' \
    -it roboticsmicrofarms/romiscan:$vtag
else
  # Start in non-interactive mode (run the command):
  docker run --runtime=nvidia --gpus all $mount_option \
    --env PYOPENCL_CTX='0' \
    roboticsmicrofarms/romiscan:$vtag \
    bash -c "$cmd"
fi