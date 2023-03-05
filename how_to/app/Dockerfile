FROM python:3.9.16-slim-bullseye

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY startup.sh startup.sh
COPY main.py main.py

CMD ["./startup.sh"]
