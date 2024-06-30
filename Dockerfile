FROM python:3.12

ADD billy /billy

RUN mkdir -p /billy/files

RUN pip install --no-cache-dir -U -r /billy/requirements.txt

CMD [ "python", "/billy/billy.py"]
