FROM node:12-alpine3.10 AS node-build

ADD MedCATtrainer/webapp/frontend /home/frontend

# Build frontend
WORKDIR /home/frontend
RUN npm install && npm rebuild node-sass && npm run build

FROM python:3.7 AS python-build

ADD MedCATtrainer/webapp/requirements.txt /home/
ADD MedCATtrainer/webapp/api /home/api


# Build backend
WORKDIR /home/api
RUN python -m venv .venv && .venv/bin/pip install --no-cache-dir -U pip setuptools wheel
RUN .venv/bin/pip install --no-cache-dir -r /home/requirements.txt && \
  .venv/bin/pip install --no-cache-dir \
  dj-database-url \
  gunicorn \
  psycopg2 \
  https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_core_sci_md-0.2.4.tar.gz && \
  find /home/api/.venv \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' \+

FROM python:3.7-slim
RUN apt-get -y update && apt-get install -y --no-install-recommends \
    libxml2 \
    libpq5 \
    nginx-light \
&&  rm -rf /var/lib/apt/lists/*

WORKDIR /home/api
COPY --from=python-build /home/api /home/api
ENV PATH="/home/api/.venv/bin:$PATH"

COPY --from=node-build /home/frontend/dist /home/frontend/dist

COPY medcat.nginx /etc/nginx/sites-available/default
COPY nginx.conf /etc/nginx
COPY medcat.run /
COPY load_examples.py run.sh /home/
RUN chmod +x /medcat.run /home/run.sh

RUN /bin/echo -en "from core.local_settings import *\n" >> /home/api/core/settings.py
COPY local_settings.py /home/api/core/


ENTRYPOINT /medcat.run
