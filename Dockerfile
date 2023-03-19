FROM python:3.11-alpine3.17

WORKDIR /usr/local/etc/chatbot
COPY ./conf/chatbot.conf.yml .

WORKDIR /opt/chatbot
COPY ./requirements.txt ./
COPY ./src/chatbot ./
RUN ["ls", "-lsah"]

RUN [ "pip", "install", "-r", "requirements.txt" ]
ENTRYPOINT [ "python", "/opt/chatbot" ]