# syntax=docker/dockerfile:1

FROM python:3.10
EXPOSE 6540

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./src .

RUN wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1cNj78NN6y2vfpBrPt-4Jz3K4y5ZFKW9l' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1cNj78NN6y2vfpBrPt-4Jz3K4y5ZFKW9l" -O weather_model.pkl && rm -rf /tmp/cookies.txt
ADD weather_model.pkl ./predictions

CMD [ "python3", "./app.py" ]
