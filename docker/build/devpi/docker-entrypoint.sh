#!/bin/bash

function defaults {
    : ${DEVPI_SERVERDIR="/data/server"}
    : ${DEVPI_CLIENTDIR="/data/client"}

    echo "DEVPI_SERVERDIR is ${DEVPI_SERVERDIR}"
    echo "DEVPI_CLIENTDIR is ${DEVPI_CLIENTDIR}"

    export DEVPI_SERVERDIR DEVPI_CLIENTDIR
}

function initialize_devpi {
    echo "[RUN]: Initializing devpi-server..."
    if [ ! -d  $DEVPI_SERVERDIR ]; then
        devpi-server --restrict-modify root --init --start --host 127.0.0.1 --port 3141
    else
        devpi-server --restrict-modify root --start --host 127.0.0.1 --port 3141
    fi
    devpi-server --status
    devpi use http://localhost:3141
    devpi login root --password=''
    DEVPI_PASSWORD=`date +%s | sha256sum | base64 | head -c 32`
    devpi user -m root password="${DEVPI_PASSWORD}"
    echo "[RUN]: devpi-server password set to '${DEVPI_PASSWORD}'" > $DEVPI_SERVERDIR/.serverpassword
    devpi index -y -c public pypi_whitelist='*'
    devpi-server --stop
    devpi-server --status
}

defaults

if [ "$1" = 'devpi' ]; then
    source /home/devpi/venvs/devpi_venv/bin/activate

    if [ ! -f  $DEVPI_SERVERDIR/.serverversion ]; then
        initialize_devpi
    fi

    echo "[RUN]: Launching devpi-server..."
    exec devpi-server --restrict-modify root --host 0.0.0.0 --port 3141
fi

echo "[RUN]: Builtin command not provided [devpi]"
echo "[RUN]: $@"

exec "$@"
