FROM python:3.11-alpine3.17

RUN apk update
RUN apk add tzdata nginx-mod-http-fancyindex nginx-mod-http-headers-more bash

ADD requirements.txt /app/
RUN python3 -m pip install -r /app/requirements.txt

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/nginx-theme /var/lib/nginx/html/nginx-theme
ADD indexer /app
COPY startup.sh /app/

WORKDIR /app
CMD ["/bin/bash", "/app/startup.sh"]

