FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/ .
COPY ./config/barn-server.cfg .

CMD [ "python","-u","./server.py", "./barn-server.cfg" ]