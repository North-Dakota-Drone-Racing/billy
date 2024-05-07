FROM python:latest

ADD billy /billy

RUN mkdir -p /billy/files

RUN pip install --no-cache-dir -U -r /billy/requirements.txt

CMD [ "python", "/billy/main.py"]