#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. By default, starts an interactive shell:
# $ ./docker/plantimager/run.sh
# $ ./run.sh -t latest -db /abs/host/my_data_base
#
# 2. Run a command:
# $ ./run.sh -t latest -db /abs/host/my_data_base -c "romi_run_task Scan my_data_base/scan_id --config /path/to/config.toml"

user=$USER
cmd=''
db_path=''
vtag="latest"
mount_option=""
cnc_device="/dev/ttyACM0"
gimbal_device="/dev/ttyACM1"

usage() {
  echo "USAGE:"
  echo "  ./run.sh [OPTIONS]
  "

  echo "DESCRIPTION:"
  echo "  Start a 'plantimager:<tag>' container, mount local (host) database and connect serial devices.
  "

  echo "OPTIONS:"
  echo "  -t, --tag
    Docker image tag to use, default to '$vtag'."
  echo "  -db, --database_path
    Host database path to mount in docker container. Require definition of docker container user."
  echo "  -u, --user
    User name in docker container, default to '$user'."
  echo "  -v, --volume
    Volume mapping for docker, e.g. '/abs/host/dir:/abs/container/dir'. Multiple use is allowed."
  echo "  -c, --cmd
    Defines the command to run at docker startup, by default start an interactive container with a bash shell."
  echo "  --cnc
    The serial port of the CNC, default to '$cnc_device'."
  echo "  --gimbal
    The serial port of the Gimbal, default to '$gimbal_device'."
  echo "  -h, --help
    Output a usage message and exit."
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
  -c | --cmd)
    shift
    cmd=$1
    ;;
  --cnc)
    shift
    cnc_device=$1
    ;;
  --gimbal)
    shift
    gimbal_device=$1
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

if [ "$cmd" = "" ]
then
    # Start in interactive mode. ~/.bashrc will be loaded.
    docker run -it $mount_option --group-add=dialout --device=$cnc_device --device=$gimbal_device plantimager:$vtag bash
else
    # Start in non-interactive mode (run the command). 
    # Request a login shell (-l) to load ~/.profile.
    docker run $mount_option --group-add=dialout --device=$cnc_device --device=$gimbal_device plantimager:$vtag bash -lc "$cmd"
fi
