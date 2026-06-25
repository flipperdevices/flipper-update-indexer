FROM python:3.11-alpine3.17

RUN apk update
RUN apk add tzdata nginx bash

ADD requirements.txt /app/
RUN python3 -m pip install -r /app/requirements.txt

COPY nginx/nginx.conf /etc/nginx/nginx.conf
ADD indexer /app
COPY startup.sh /app/

WORKDIR /app
CMD ["/bin/bash", "/app/startup.sh"]

