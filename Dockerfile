FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY requirements.txt /tmp/
RUN pip install -U pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./musocial /app
COPY setup.py /tmp/
RUN ln -s /app /tmp/musocial

RUN pip install --no-cache-dir -e /tmp/

COPY config.py /app/
COPY prestart.sh /app/

ENV INSTANCE_PATH=/instance
VOLUME ["/instance"]
