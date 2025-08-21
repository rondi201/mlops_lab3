#!/bin/bash
usage="$(basename "$0") [-h] [-s <message>] -- program to run alembic database revision

where:
    -h  show this help text
    -e  dotenv file to run main docker compose 
    -m  message of revision (usage in alembic revision -m <message>)"

commit_message=""
env_file=".env"
while getopts ':hme:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    s) commit_message=$OPTARG
       ;;
    e) env_file=$OPTARG
       ;;
    :) printf "missing argument for -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
   \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done


docker compose \
    --env-file ${env_file} \
    run --build --rm \
    -v ${PWD}/alembic/versions:alembic/versions \
    api \
    bash -c """alembic upgrade head && alembic revision --autogenerate -m '${commit_message}'"""