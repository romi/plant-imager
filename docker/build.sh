#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. Default build options will create `romiscanner:latest`:
# $ ./build.sh
#
# 2. Build image with 'debug' tag & another 'romiscanner' branch 'feature/LpyIntegration' options:
# $ ./build.sh -t debug -b feature/LpyIntegration
#
# 3. Build image with 'debug' tag & other specific branches
# $ ./build.sh -t debug --romiscanner specific_branch_of_romiscanner --romiscan specific_branch_of_romiscan --romidata specific_branch_of_romidata

vtag="latest"
romidata_branch='dev'
romiscan_branch='dev'
romiscanner_branch='master'
user=$USER
uid=$(id -u)
group=$(id -g -n)
gid=$(id -g)
docker_opts=""

usage() {
  echo "USAGE:"
  echo "  ./build.sh [OPTIONS]
    "

  echo "DESCRIPTION:"
  echo "  Build a docker image named 'romiscanner' using Dockerfile in same location.
    "

  echo "OPTIONS:"
  echo "  -t, --tag
    Docker image tag to use, default to '$vtag'.
    "
  echo "  -u, --user
    User name to create inside docker image, default to '$user'.
    "
  echo "  --uid
    User id to use with 'user' inside docker image, default to '$uid'.
    "
  echo "  -g, --group
    Group name to create inside docker image, default to 'group'.
    "
  echo "  --gid
    Group id to use with 'user' inside docker image, default to '$gid'.
    "
  echo "  --romiscan
    Git branch to use for cloning 'romiscan' inside docker image, default to '$romiscan_branch'.
    "
  echo "  --romidata
    Git branch to use for cloning 'romidata' inside docker image, default to '$romidata_branch'.
    "
  echo "  -b, --romiscanner
    Git branch to use for cloning 'romiscanner' inside docker image, default to '$romiscanner_branch'.
    "
  # Docker options:
  echo "  --no-cache
    Do not use cache when building the image, (re)start from scratch.
    "
  echo "  --pull
    Always attempt to pull a newer version of the parent image.
    "
  # General options:
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
  -b | --romiscanner)
    shift
    romiscanner_branch=$1
    ;;
  --romiscan)
    shift
    romiscan_branch=$1
    ;;
  --romidata)
    shift
    romidata_branch=$1
    ;;
  --no-cache)
    shift
    docker_opts="$docker_opts --no-cache"
    ;;
  --pull)
    shift
    docker_opts="$docker_opts --pull"
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

# Get the date to estimate docker image build time:
start_time=`date +%s`

# Start the docker image build:
docker build -t romiscanner:$vtag $docker_opts \
  --build-arg ROMISCAN_BRANCH=$romiscan_branch \
  --build-arg ROMIDATA_BRANCH=$romidata_branch \
  --build-arg ROMISCANNER_BRANCH=$romiscanner_branch \
  --build-arg USER_NAME=$user \
  --build-arg USER_ID=$uid \
  --build-arg GROUP_NAME=$group \
  --build-arg GROUP_ID=$gid \
  -f docker/Dockerfile .

# Print docker image build time:
echo
echo Build time is $(expr `date +%s` - $start_time) s
