if [ ! -d /mnt/virtualenvs/"$JOB_NAME" ]; then
    mkdir -p /mnt/virtualenvs/"$JOB_NAME"
    virtualenv --system-site-packages /mnt/virtualenvs/"$JOB_NAME"
fi

export PIP_DOWNLOAD_CACHE=/mnt/pip-cache

. /mnt/virtualenvs/"$JOB_NAME"/bin/activate

cd configuration
pip install -r requirements.txt
