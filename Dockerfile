FROM python:3.10
EXPOSE 6540

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./src .

COPY download_model.sh download_model.sh
RUN chmod +x download_model.sh
RUN download_model.sh

CMD [ "python3", "./app.py" ]