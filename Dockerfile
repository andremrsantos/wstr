FROM python:alpine

COPY . /app
WORKDIR /app

RUN apk --update add linux-headers pcre-dev && \
    apk --update --no-cache add --virtual build-dependencies \
    build-base gcc && \
    make -C resource/structure_src/ clean && \
    make -C resource/structure_src/ all && \
    python setup.py install && \
    apk del build-dependencies && \
    rm -rf /var/cache/apk/*

ENV APP_PATH /app
EXPOSE 5000
CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]