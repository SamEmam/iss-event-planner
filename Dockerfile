FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
COPY event_data.json /data/event_data.json

CMD ["python3", "app.py"]