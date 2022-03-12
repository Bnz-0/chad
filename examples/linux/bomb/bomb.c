#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

// Hi {{ github_username }}, this is your challenge

void print_flag()
{
	system("cat flag.txt");
}

void goBoom()
{
	printf("BOOM!\n\nYou failed.\n");
	exit(0);
}

void functionZero(char *buffer)
{
	if (strcmp(buffer, "{{ foo0_sol }}") != 0) {
		goBoom();
	}
}

void functionOne(char *buffer)
{
	int magicNumber = {{ rand_scanf_safe_int() | saveas('foo1_sol') }};
	if (*(int *) buffer != magicNumber) {
		goBoom();
	}
}

void functionTwo(char *buffer)
{
	int i = 0;
	char string[] = "{{ rand_str(10,15, alpha_uppercase) | saveas('foo2_sol') }}";
	const size_t len = strlen(string);
	for (i = 0; i < len; i++) {
		if (string[i] != buffer[i]) {
			goBoom();
		}
	}
}

void functionThree(char *buffer)
{
	if (strlen(buffer) > 3)
		goBoom();
	int one = atoi(buffer);
	if ({{ IntPolynomial(foo3_sol).to_str('one') }} == 0) {
		printf("You're getting better!\n");
	} else {
		goBoom();
	}
}

void functionFour(char *buffer)
{
	char buffer2[10];
	strncpy(buffer2, buffer, 10);
	printf("Validating Input 4\n");
	if (buffer2[0] + buffer2[8] == {{ foo4_sol[0]+foo4_sol[8] }}) {
		if (buffer2[1] + buffer2[7] == {{ foo4_sol[1]+foo4_sol[7] }}) {
			if (buffer2[2] + buffer2[6] == {{ foo4_sol[2]+foo4_sol[6] }}) {
				if (buffer2[3] + buffer2[5] == {{ foo4_sol[3]+foo4_sol[5] }}) {
					if (buffer2[4] == {{ foo4_sol[4] }})
						printf("Good job.\n");
				} else
					goBoom();
			} else
				goBoom();
		} else
			goBoom();
	} else
		goBoom();
}

int main()
{
	char buffer[64];
	void (*functionArray[])(char *) =
		{ &functionZero, &functionOne, &functionTwo, &functionThree,
	&functionFour };
	void (*func)(char *);
	int i;
	setvbuf(stdout, NULL, _IONBF, 0);
	printf("Hi!\nI am a BOMB!\nGive me the right inputs or I'll explode.\n");
	for (i = 0; i < 5; i++) {
		printf("Enter input #%d: ", i + 1);
		scanf("%s", buffer);
		func = functionArray[i];
		func(buffer);
	}
	print_flag();
	return 0;
}
