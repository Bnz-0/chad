EXES = bomb
CFLAGS = -fno-pie -no-pie -fno-stack-protector -fno-omit-frame-pointer -fcf-protection=none -U_FORTIFY_SOURCE -Wall -Werror

all: $(EXES)

bomb: bomb.c
	$(CC) $(CFLAGS) -m32 -o $@ $^
	strip $@

clean:
	rm -f $(EXES)

.PHONY: clean
