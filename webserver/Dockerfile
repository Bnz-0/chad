FROM ubuntu:20.04
RUN apt-get update -y && apt-get install -y python3-pip python3-dev
WORKDIR /app
RUN pip3 install Jinja2 ansicolors flask requests
COPY index.html /app
COPY webserver.py /app
CMD [ "python3", "webserver.py" ]
