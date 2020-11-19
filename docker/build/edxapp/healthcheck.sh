if [ `curl -s -o /dev/null -w "%{http_code}" localhost:$1/heartbeat` -ne 200 -o `curl -s -o /dev/null -w "%{http_code}" localhost:$1/$2` -ne 200 ]; then
    exit 1
fi
