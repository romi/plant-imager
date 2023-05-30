#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. By default, starts an interactive shell:
# $ ./docker/virtualplantimager/run.sh
# $ ./run.sh -t latest -db /abs/host/my_data_base -v /abs/host/dir:/abs/container/dir
#
# 2. Run a command:
# $ ./run.sh -t latest -db /abs/host/my_data_base -v /abs/host/dir:/abs/container/dir -c "romi_run_task --config /path/to/config.toml VirtualScan my_data_base/scan_id"

# - Defines colors and message types:
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color
INFO="${GREEN}INFO${NC}    "
WARNING="${YELLOW}WARNING${NC} "
ERROR="${RED}ERROR${NC}   "
bold() { echo -e "\e[1m$*\e[0m"; }

# - Default variables
# Image tag to use, 'latest' by default:
vtag="latest"
# Command to execute after starting the docker container:
cmd=''
# Volume mounting options:
mount_option=""
# If the `DB_LOCATION` variable is set, use it as default database location, else set it to empty:
if [ -z ${DB_LOCATION+x} ]; then
  echo -e "${WARNING}Environment variable DB_LOCATION is not defined, set it to use as default database location!"
  host_db=''
else
  host_db=${DB_LOCATION}
fi

usage() {
  echo "$(bold USAGE):"
  echo "  ./run.sh [OPTIONS]"
  echo ""

  echo "$(bold DESCRIPTION):"
  echo "  Start a docker container using the 'roboticsmicrofarms/virtualplantimager' image."
  echo ""

  echo "$(bold OPTIONS):"
  echo "  -t, --tag
    Image tag to use." \
    "By default, use the '${vtag}' tag."
  echo "  -db, --database
    Path to the host database to mount inside the docker container." \
    "By default, use the 'DB_LOCATION' environment variable (if defined)."
  echo "  -v, --volume
    Volume mapping between host and container to mount a local directory in the container." \
    "Absolute paths are required and multiple use of this option is allowed." \
    "For example '-v /host/dir:/container/dir' makes the '/host/dir' directory accessible under '/container/dir' within the container."
  echo "  -c, --cmd
    Defines the command to run at container startup." \
    "By default, start an interactive container with a bash shell."
  echo "  -h, --help
    Output a usage message and exit."
}

while [ "$1" != "" ]; do
  case $1 in
  -t | --tag)
    shift
    vtag=$1
    ;;
  -db | --database)
    shift
    host_db=$1
    ;;
  -v | --volume)
    shift
    if [ "${mount_option}" == "" ]; then
      mount_option="-v $1"
    else
      mount_option="${mount_option} -v $1" # append
    fi
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

# Use local database path `$host_db` to create a bind mount to '/myapp/db':
if [ "${host_db}" != "" ]; then
  mount_option="${mount_option} -v ${host_db}:/myapp/db"
  echo -e "${INFO}Automatic bind mount of '${host_db}' (host) to '/myapp/db' (container)!"
else
  echo -e "${ERROR}No local host database defined!"
  echo -e "${INFO}Set 'DB_LOCATION' or use the '-db' | '--database' option to define it."
  exit 1
fi

# Check if we have a TTY or not
if [ -t 1 ]; then
  USE_TTY="-it"
else
  USE_TTY=""
fi

if [ "${cmd}" = "" ]; then
  # Start in interactive mode. ~/.bashrc will be loaded.
  docker run --rm --gpus all ${mount_option} \
    ${USE_TTY} roboticsmicrofarms/virtualplantimager:${vtag} \
    bash
else
  # Get the date to estimate command execution time:
  start_time=$(date +%s)
  # Start in non-interactive mode (run the command).
  # Request a login shell (-l) to load ~/.profile.
  docker run --rm --gpus all ${mount_option} \
    ${USE_TTY} roboticsmicrofarms/virtualplantimager:${vtag} \
    bash -lc "${cmd}"
  # Get command exit code:
  cmd_status=$?
  # Print build time if successful (code 0), else print command exit code
  if [ ${cmd_status} == 0 ]; then
    echo -e "\n${INFO}Command SUCCEEDED in $(expr $(date +%s) - ${start_time})s!"
  else
    echo -e "\n${ERROR}Command FAILED after $(expr $(date +%s) - ${start_time})s with code ${cmd_status}!"
  fi
  # Exit with status code:
  exit ${cmd_status}
fi
