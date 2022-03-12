EXES = hello_world
CFLAGS = -Wall -Werror

all: $(EXES)

hello_world: hello_world.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(EXES)

.PHONY: clean
