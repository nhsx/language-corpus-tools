FROM python:3.9-slim

RUN pip install scrapy psycopg2-binary txpostgres python-dateutil treq atoma
RUN mkdir /scrapy
WORKDIR /scrapy
COPY ./corpus ./corpus
COPY ./scrapy.cfg ./run.py ./
RUN chmod +x ./run.py
CMD ./run.py
