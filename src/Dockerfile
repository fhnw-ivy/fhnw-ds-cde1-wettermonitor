# syntax=docker/dockerfile:1

FROM python:3.9.15
EXPOSE 6540

WORKDIR /app

RUN pip install pandas

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY .. .

CMD [ "python3", "./app.py" ]
