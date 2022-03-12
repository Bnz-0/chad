FROM manjarolinux/base:latest
COPY . /site
WORKDIR /site
RUN yes | pacman -S php php-sqlite
RUN cat init.sql | sqlite3 database.sqlite
CMD [ "php", "-S", "0.0.0.0:8080", "-c", "php.ini" ]
