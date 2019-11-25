Example:
$ docker build . -t edxops/flower:latest
$ docker run -it --rm -p 127.0.0.1:5555:5555 edxops/flower:latest flower --broker=redis://:@some-redis-url.com:6379 --conf=flowerconfig.py

$ curl localhost:5555


Example with oauth:
docker run -it --rm -p 127.0.0.1:5555:5555   -e OAUTH2_KEY="xxxyyy.apps.googleusercontent.com" -e OAUTH2_SECRET="xxxxx" -e OAUTH2_REDIRECT_URI="flower-url.com/login" -e AUTH=".*@domain.org" edxops/flower:latest flower --broker=redis://myuser:mypass@my-redis.com:6379
