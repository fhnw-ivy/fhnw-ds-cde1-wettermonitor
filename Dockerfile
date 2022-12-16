FROM python:3.10
EXPOSE 6540

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./src .
COPY ./prediction/*.pkl ./prediction

CMD [ "python3", "./app.py" ]
