Example:
$ docker build . -t edxops/flower:latest
$ docker run -it --rm -p 127.0.0.1:5555:5555 edxops/flower:latest flower --broker=redis://:@some-redis-url.com:6379 --conf=flowerconfig.py

$ curl localhost:5555
