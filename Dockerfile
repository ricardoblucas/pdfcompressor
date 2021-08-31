# syntax=docker/dockerfile:1

FROM python:3.7-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt\ 
  && apt-get update\
  && apt-get install -y ghostscript\
  && apt-get clean


COPY . .

EXPOSE 80

ENV LISTEN_PORT=80

ENTRYPOINT ["./gunicornstart.sh"]
# CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=80"]
