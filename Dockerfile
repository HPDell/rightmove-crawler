FROM python:3.8

COPY . /srv
WORKDIR /srv

RUN pip install -r requirements.txt

ENTRYPOINT [ "startup.sh" ]