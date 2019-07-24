FROM python:alpine

COPY . /app
WORKDIR /app

ENV STRUCTURE_LINK http://web.stanford.edu/group/pritchardlab/structure_software/release_versions/v2.3.4/structure_kernel_source.tar.gz
ENV STRUCTURE_FOLDER structure_kernel_src
ENV STRUCTURE $STRUCTURE_FOLDER/structure

RUN apk --update add sqlite-dev linux-headers pcre-dev && \
    apk --update --no-cache add --virtual build-dependencies \
    build-base gcc && \
    wget $STRUCTURE_LINK && \
    tar -xvzf structure_kernel_source.tar.gz && \
    make -C $STRUCTURE_FOLDER clean && \
    make -C $STRUCTURE_FOLDER all && \
    python setup.py install && \
    apk del build-dependencies && \
    rm -rf /var/cache/apk/*

ENV APP_PATH /app
EXPOSE 5000
CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]