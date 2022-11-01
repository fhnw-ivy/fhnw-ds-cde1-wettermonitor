# syntax=docker/dockerfile:1

FROM python:3.10
EXPOSE 6540

WORKDIR /app

RUN pip install --upgrade pip
RUN pip3 install influxdb
RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install requests
RUN pip3 install Flask

COPY .. .

CMD [ "python3", "./app.py" ]
