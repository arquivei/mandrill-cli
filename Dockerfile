FROM python:3.7-alpine as base

FROM base

RUN addgroup -g 1000 mandrill && \
    adduser -u 1000 -G mandrill -h /home/mandrill -D mandrill

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

USER mandrill
WORKDIR /home/mandrill
COPY mandrill.py .

ENTRYPOINT [ "/home/mandrill/mandrill.py" ]