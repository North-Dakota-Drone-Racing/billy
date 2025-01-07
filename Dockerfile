FROM python:3.12

ADD . /billy

RUN mkdir -p /billy/files

RUN pip install poetry

WORKDIR /billy

RUN poetry install

CMD [ "poetry", "run", "start-billy"]
