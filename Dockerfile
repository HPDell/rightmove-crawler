FROM python:3.8

COPY . /srv
WORKDIR /srv
RUN chmod +x startup.sh

RUN pip install -r requirements.txt
EXPOSE 8000

ENTRYPOINT [ "/bin/bash", "startup.sh" ]