@echo off
setlocal EnableDelayedExpansion
set \n=^
%==%


set usage=^
  %~nx0 [-h] [-m ^<message^>] -- program to run alembic database revision!\n!!\n!^
    where:!\n!^
      -h  show this help text!\n!^
      -e  dotenv file to run main docker compose!\n!^
      -m  message of revision (usage in alembic revision -m ^<message^>)

set commit_message=
set env_file=

:parse_args
if "%~1"=="" goto execute_command

if "%~1"=="-h" (
    echo !usage!
    exit /b 0
)

if "%~1"=="-m" (
    if "%~2"=="" (
        echo Error: Missing argument for -m
        echo !usage!
        exit /b 1
    )
    set "commit_message=%~2"
    shift
    shift
    goto parse_args
)

if "%~1"=="-e" (
    if "%~2"=="" (
        echo Error: Missing argument for -e
        echo !usage!
        exit /b 1
    )
    set "env_file=%~2"
    shift
    shift
    goto parse_args
)

echo Error: Illegal option: %~1
echo !usage!
exit /b 1

:execute_command
if "%commit_message%"=="" (
    echo Error: Commit message is required
    echo !usage!
    exit /b 1
)
if "%env_file%"=="" (
    echo Error: Dotend file is required
    echo !usage!
    exit /b 1
)

docker compose^
    --env-file %env_file%^
    run --build --rm^
    -v "%cd%/alembic/versions:/app/alembic/versions"^
    api bash -c "alembic upgrade head && alembic revision --autogenerate -m '%commit_message%'"

endlocal