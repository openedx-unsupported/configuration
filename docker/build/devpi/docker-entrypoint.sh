#!/bin/bash

function defaults {
    : ${DEVPISERVER_SERVERDIR="/data/server"}
    : ${DEVPI_CLIENTDIR="/data/client"}

    echo "DEVPISERVER_SERVERDIR is ${DEVPISERVER_SERVERDIR}"
    echo "DEVPI_CLIENTDIR is ${DEVPI_CLIENTDIR}"

    export DEVPISERVER_SERVERDIR DEVPI_CLIENTDIR
}

function initialize_devpi {
    echo "[RUN]: Initializing devpi-server..."
    DEVPI_PASSWORD=`date +%s | sha256sum | base64 | head -c 32`
    devpi-init --root-passwd ${DEVPI_PASSWORD}
    echo "[RUN]: devpi-server password set to '${DEVPI_PASSWORD}'" > $DEVPISERVER_SERVERDIR/.serverpassword
}

defaults

if [ "$1" = 'devpi' ]; then
    source /home/devpi/venvs/devpi_venv/bin/activate

    if [ ! -f  $DEVPISERVER_SERVERDIR/.serverversion ]; then
        initialize_devpi
    fi

    echo "[RUN]: Launching devpi-server..."
    exec devpi-server --restrict-modify root --host 0.0.0.0 --port 3141
fi

echo "[RUN]: Builtin command not provided [devpi]"
echo "[RUN]: $@"

exec "$@"
