FROM python:3.9.1-slim-buster
WORKDIR /app
RUN apt-get update && apt-get -y install gcc
COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt
COPY . .
RUN mkdir /socket
RUN chown -R www-data:www-data /app /socket
EXPOSE 3000
CMD ["uwsgi", "--ini", "uwsgi.ini", "--http-socket", ":3000"]
