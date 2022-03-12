#!/bin/env python3
from pwn import *
context.log_level = 'debug'

sh = process("./bomb")
sh.recvuntil("#1:")
sh.sendline("{{ foo0_sol }}")
sh.recvuntil("#2:")
sh.sendline(p32({{ foo1_sol }}))
sh.recvuntil("#3:")
sh.sendline("{{ foo2_sol }}")
sh.recvuntil("#4:")
sh.sendline("{{ foo3_sol[0] }}")
sh.recvuntil("#5:")
sh.sendline(
	p8({{ foo4_sol[0] }}) +
	p8({{ foo4_sol[1] }}) +
	p8({{ foo4_sol[2] }}) +
	p8({{ foo4_sol[3] }}) +
	p8({{ foo4_sol[4] }}) +
	p8({{ foo4_sol[5] }}) +
	p8({{ foo4_sol[6] }}) +
	p8({{ foo4_sol[7] }}) +
	p8({{ foo4_sol[8] }})
)

sh.recvuntil('}')
sh.close()
