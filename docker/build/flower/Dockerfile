FROM ubuntu:xenial

# Update and get pip.
RUN apt-get update && apt-get install -y python3-pip

# Install the required packages
RUN pip3 install --no-cache-dir redis==2.10.6 celery==3.1.18 flower==0.9.2

# PYTHONUNBUFFERED: Force stdin, stdout and stderr to be totally unbuffered. (equivalent to `python -u`)
# PYTHONHASHSEED: Enable hash randomization (equivalent to `python -R`)
# PYTHONDONTWRITEBYTECODE: Do not write byte files to disk, since we maintain it as readonly. (equivalent to `python -B`)
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1

# Default port
EXPOSE 5555

RUN apt-get install bash -qy

# Run as a non-root user by default, run as user with least privileges.
USER nobody

# Mount a config here if you want to enable OAuth etc
ADD docker/build/flower/flowerconfig.py /flowerconfig.py

ENTRYPOINT [ "flower" ]
