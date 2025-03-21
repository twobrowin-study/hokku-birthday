FROM python:3.12-slim-bullseye

WORKDIR /python-docker

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY python/*.py ./

CMD [ "python3", "-u", "main.py"]