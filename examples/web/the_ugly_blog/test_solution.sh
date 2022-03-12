#!/bin/bash

cat init.sql | sqlite3 database.sqlite

php -S localhost:8080 -c php.ini &
pid=$!
sleep 1

bash solution.sh localhost:8080

kill $pid
rm database.sqlite
