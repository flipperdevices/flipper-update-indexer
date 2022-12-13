FROM python:3.11-alpine3.17

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/nginx-theme /etc/nginx/nginx-theme
ADD indexer /app
COPY startup.sh /app/
WORKDIR /app

RUN apk update
RUN apk add tzdata nginx-mod-http-fancyindex bash
RUN python3 -m pip install -r requirements.txt

CMD ["/bin/bash", "startup.sh"]
