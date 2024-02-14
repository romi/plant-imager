#!/bin/bash
###############################################################################
# Usage examples:
# --------------
# 1. Start a container with an interactive shell:
# $ ./docker/virtualplantimager/run.sh
#
# 2. Start a container, run a command and exit the container:
# $ ./docker/virtualplantimager/run.sh -c "romi_run_task VirtualScan $ROMI_DB/scan_id  --config /path/to/config.toml"
###############################################################################

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
# Default group id to use when starting the container:
gid=2020
# Image tag to use, 'latest' by default:
vtag="latest"
# Command to execute after starting the docker container:
cmd=''
# Volume mounting options:
mount_option=""
# Test configuration is blender server with LPY model:
test_cfg="plant-imager/configs/vscan_lpy_blender.toml"
# Test command:
test_cmd="romi_run_task VirtualScan /myapp/db/vplant_test --config ${test_cfg}"
# Defines the temporary directory to use (in case of test and no path to local database)
tmp_dir="/tmp/ROMI_DB/"

# If the `ROMI_DB` variable is set, use it as default database location, else set it to empty:
if [ -z ${ROMI_DB+x} ]; then
  echo -e "${WARNING}Environment variable 'ROMI_DB' is not defined, set it to use as default database location!"
  host_db=''
else
  host_db=${ROMI_DB}
fi

usage() {
  echo -e "$(bold USAGE):"
  echo "  ./docker/virtualplantimager/run.sh [OPTIONS]"
  echo ""

  echo -e "$(bold DESCRIPTION):"
  echo "  Start a docker container using the 'roboticsmicrofarms/virtualplantimager' image."
  echo ""

  echo -e "$(bold OPTIONS):"
  echo "  -t, --tag
    Image tag to use." \
    "By default, use the '${vtag}' tag."
  echo "  -db, --database
    Path to the host database to mount inside the docker container." \
    "By default, use the 'ROMI_DB' environment variable (if defined)."
  echo "  -v, --volume
    Volume mapping between host and container to mount a local directory in the container." \
    "Absolute paths are required and multiple use of this option is allowed." \
    "For example '-v /host/dir:/container/dir' makes the '/host/dir' directory accessible under '/container/dir' within the container."
  echo "  -c, --cmd
    Defines the command to run at container startup." \
    "By default, start an interactive container with a bash shell."
  echo "  --test
    Test the 'VirtualScan' task with the default config '${test_cfg}'."
  echo "  --tmp
    Create a temporary database under '${tmp_dir}'."
  echo "  -h, --help
    Output a usage message and exit."
}

bind_mount_options() {
  mount_option="${mount_option} -v ${host_db}:/myapp/db"
}

create_tmp_db() {
  # If an argument is provided, use it as host database, else use the temporary path defined in $tmp_dir,
  if [ "$1" != "" ]; then
    host_db="$1"
  else
    host_db="${tmp_dir}"
  fi
  # Create the directory 'vplant_test':
  mkdir -p "${host_db}/vplant_test"
  # Add the marker to be a valid plantdb database:
  touch "${host_db}/romidb"
  # Copy the 'vscan_data' required to run the `VirtualScan` task:
  cp -r "database_example/vscan_data/" "${host_db}/"
}

test=0
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
  --test)
    cmd="${test_cmd}"
    test=1
    ;;
  --tmp)
    create_tmp_db ""
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

if [ ${test} == 1 ]; then
  create_tmp_db "${host_db}"
fi

# Use local database path `$host_db` to create a bind mount to '/myapp/db':
if [ "${host_db}" != "" ]; then
  bind_mount_options
  echo -e "${INFO}Automatic bind mount of '${host_db}' (host) to '/myapp/db' (container)!"
else
  # Else raise an error:
  echo -e "${WARNING}No local host database defined!"
  echo -e "${INFO}Set 'ROMI_DB' or use the '-db' | '--database' option to define it."
fi

# If a 'host database path' is provided, get the name of the group and its id to, later used with the `--user` option
if [ "${host_db}" != "" ]; then
  group_name=$(stat -c "%G" ${host_db})                              # get the name of the group for the 'host database path'
  gid=$(getent group ${group_name} | cut --delimiter ':' --fields 3) # get the 'gid' of this group
  echo -e "${INFO}Automatic group id definition to '$gid'!"
else
  echo -e "${WARNING}Using default group id '${gid}'."
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
    --user romi:${gid} \
    ${USE_TTY} \
    roboticsmicrofarms/virtualplantimager:${vtag} \
    bash
else
  echo -e "${INFO}Running: '${cmd}'."
  echo -e "${INFO}Bind mount: '${mount_option}'."
  echo -e "  docker run --rm --gpus all ${mount_option} \
    --user romi:${gid} \
    ${USE_TTY} \
    roboticsmicrofarms/virtualplantimager:${vtag} \
    bash -c ${cmd}"
  # Get the date to estimate command execution time:
  start_time=$(date +%s)
  # Start in non-interactive mode (run the command).
  # Request a login shell (-l) to load ~/.profile.
  docker run --rm --gpus all ${mount_option} \
    --user romi:${gid} \
    ${USE_TTY} \
    roboticsmicrofarms/virtualplantimager:${vtag} \
    bash -c "${cmd}"
  # Get command exit code:
  cmd_status=$?

  # Print elapsed time if successful (code 0), else print command exit code
  elapsed_time=$(expr $(date +%s) - ${start_time})
  if [ ${cmd_status} == 0 ]; then
    echo -e "\n${INFO}Command SUCCEEDED in ${elapsed_time}s!"
  else
    echo -e "\n${ERROR}Command FAILED after ${elapsed_time}s with code ${cmd_status}!"
  fi
  # Exit with status code:
  exit ${cmd_status}
fi
