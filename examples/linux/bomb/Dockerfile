FROM zxgio/pwn-jail:focal-20210416
COPY flag.txt /new_root
COPY bomb /new_root/chall
RUN chmod 444 /new_root/flag.txt
RUN chmod 555 /new_root/chall
