# chad.py — CHallenge Automation and Deployment

**Chad** is a CLI tool born from the necessity to generate multiple CTF-like
challenges for educational purposes; that is, each challenge must be similar
to the others but different.

## Installation

```bash
# clone the repo
git clone https://github.com/Bnz-0/chad.git
cd chad

# install the requirements
pip3 install --user -r requirements.txt

./chad.py --help
```

## Challenges generation

> TL;DR
>
> See an [example](examples) and the [command line interface](#command-line-interface).

To generate multiple different challenges, **chad** starts from a _challenge template_,
which is simply a folder that can contains [any kind of file](#rendered-files)
necessary to the final challenge, and the [_steps_ subfolder](#steps).
To generate a challenge from the template, **chad** first copy the whole content
of the folder in the destination, then step-by-step it renders the files specified
in the [_step scripts_](#steps) with [Jinja](https://jinja.palletsprojects.com/en/3.0.x/).

Chad iterates this process as many times as needed to generate _N_ different
challenges. The differences between two generated challenges depend on the challenge
template: the more "randomness" the author puts in, the more differences there are.

### Rendered files

Any file in the template folder will be rendered by using the
[Jinja](https://jinja.palletsprojects.com/en/3.0.x/) template engine; this grants
a lot of flexibility.

In the Jinja template (i.e. any file in the _challenge template folder_) you can
use any variables declared in the _step scripts_, and a series of utility
built-in functions that you can find in [context.py](context.py).

Those utility functions are useful to randomize stuff; for example, the size of
a buffer or a particular value:

```c
char buf[{{ rand_int(100, 200) }}];
int x = {{ choose_one(hexspeak) }};
```

Which may generate code like this:

```c
char buf[123];
int x = 0xc0ffe;
```

There are also specific functions that cover some annoying problems; for instance,
generating a random integer whose bytes do not correspond to any whitespace
characters:

```c
int magicNumber = {{ rand_scanf_safe_int() }};
scanf("%s", buffer);
if(*(int*)buffer == magicNumber) puts("You won!");
```

> Useful references:
>
> - [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/)
> - [Utility built-in functions](context.py)

### Steps

In the _steps_ subfolder there are one or more _step script_, which are simply
Python scripts that will be evaluated by **chad** in **alphabetical order**.
Those scripts are used to force an order on the rendering of the other files,
giving more flexibility in the generation process.

So, with a _steps_ folder with three files:

```
steps
├── 0.py
├── 1.py
└── 2.py
```

**Chad** will:

1. evaluate `0.py` \
    1.1 render each file specified in `0.py`
2. evaluate `1.py` \
    2.1 render each file specified in `1.py`
3. evaluate `2.py` \
    3.1 render each file specified in `2.py`

To specify which files to render, set the special (optional) variable: `_files`,
which is used to specify a list of files that you want to render in the corresponding
step.
For example:

```python
_files = ["challenge.c", "flag.txt"]
```

Or something like that:

```python
_files = ["*.php", "some_folder/*.sql"]
```

If this variable in not present, its default value is an empty list; that is,
no file will be rendered in that step.

A _step script_ serves not only to force a rendering order. Any variable that you
declare in those Python scripts will be available in the following steps.

For example, if you set variable `x = 42` in `1.py`, then it is possible to use
`x` in step file `2.py`, and in any files rendered by steps `1.py` and `2.py`.

**Notice: those scripts are `eval()`uated by chad! This means that any code
inside will be executed without any restriction.**

### Command line interface

Once a template is ready, generating the challenges is pretty simple. The `generate`
subcommand support various arguments (see `./chad.py generate --help`), but only 2
are needed mandatory: the number of challenges and the template path.

For example, to generate 5 challenges from the [`bomb`](examples/linux/bomb) template,
storing the results in the `challs` folder:

```sh
./chad.py generate -n5 examples/linux/bomb -o challs
```

> Notice: you need [pwntools](https://docs.pwntools.com/en/stable/install.html#python3)
> to run the `sol.py` script and test the generated chllenge

Alternatively with `-f`, we can use an _instances_ file, which should specify the
challengers that will have to solve the generated challenges:

```sh
./chad.py generate -f examples/instances.csv examples/linux/bomb -o challs
```

> Notice: **any value of an instance file will be available as well in the templates**.
>
> For example it is possible to use the `{{github_username}}` variable since in the
> [instances.csv](examples/instances.csv) there is the "github_username" column
> for each instance.

Now, in the `challs` folder there are the generated challenges.
Take a look of what **chad** generated.

### Test the generated challenges

A huge problem in randomly generating multiple challenges from a template is that
some of them could be unsolvable for a variety of reasons (e.g. a byte corresponding
to a newline in a memory address).
So, it is a good practice to generate not only the challenges, but also a script
to solve them.
By doing this, we can use the last _step_ to run the script and make sure that
every generated challenge is indeed solvable.

For instance, in the [bomb](examples/linux/bomb) example there are 3 steps.
The first two are for generating the source code, both for the challenge
itself and for its solution: `sol.py`.
Then, a third one ([`2.py`](examples/linux/bomb/steps/2.py)) compiles the C
source code and then run `sol.py` to check the solution:

```python
import os
os.system("make")
check_solution("python3 sol.py", flag)
```

The `flag` variable was set in a previous _step_ ([`0.py`](examples/linux/bomb/steps/0.py)),
and `check_solution` is just a function (from the [utilities](context.py)) that
runs a command and checks for the flag in its output.

## Deployment

**Chad** can also help in automating the deployment phase. It is not mandatory, of
course, but it is really useful when there is the necessity to expose the
challenges trough a remote server.

There are countless ways to deploy a challenge, **chad** uses a mix of docker
containers, VPN and firewall rules. The idea is:

- Each challenge lives (sandboxed) inside a container
- All challenges will be exposed only on a VPN such that:
  - Each user will have a fixed IP address inside the VPN (corresponding to
    a personal certificate)
  - Each user will be able to see only their challenges

The files, needed to create a server to deploy the challenges,
can be generated by **chad**.

> The requirements for the server are: [docker](https://www.docker.com/),
> [wireguard](https://www.wireguard.com/) as VPN, and
> [iptables](https://git.netfilter.org/iptables/) as firewall.
>
> **Since chad only generate the configuration files, those requirements are
> needed only on the server**

First, we need to put a _piece_ of docker-compose file in the challenge template(s)
(see the [bomb one](examples/linux/bomb/docker-compose.yml) for example).
These pieces will be merged in a final `docker-compose.yml` file, allowing us
to start/stop all generated challenges at once.

Then, we can create the file needed to run the server:

```sh
mkdir server
cd server
../chad.py init
```

The `init` subcommand initializes the JSON configuration, used to generate
all other files. Note: chad expects Wireguard to be installed.

The settings are:

- **interface**: the name of the wireguard interface
- **endpoint**: the endpoint of the VPN
- **subnet**: the subnet of the VPN
- **pubkey**: the public key of the VPN server (if it is not valid, then **chad**
  will ask you if you want to to generate it)
- **base_port**: the starting port where to expose the challenges
- **port_range**: how many ports to reserve for each user
- **cert_folder**: the folder where to place the wireguard certificates
- **rules_folder**: the folder where to place the scripts for iptables
- **user_database**: the name of the file that will be used to take track of
  all the instances, their ports, IP address and other optional information

After that it will be possible to use the `setup` command:

```sh
../chad.py setup -f ../examples/instances.csv conf.json
```

This will initialize all necessary files, using the `conf.json` file
(created by the `init` command), and an instance file, which lists the
users to include in the VPN.

> It is possible to run `setup` again with another instance file: chad
> will only add the new users, that is, users that are not already present.

At this point it is possible to generate the challenges
**using the "user_database" file** generated by **chad** as instances:

```sh
cd ..
./chad.py generate -f server/user.json --docker-compose --param port_offset=0 examples/linux/bomb -o server/challs
```

The option `--docker-compose` tells **chad** to concatenate the docker-compose files,
and `--param port_offset=0` is adding a variable that we can use inside the
docker-compose to decide which port to use for this challenge.

This will work also with multiple templates, but from the command line it would
be a nightmare. Instead of passing the template folder, it is possible to use a
JSON file to specify all templates we want to generate. See [challs.json](examples/challs.json).

Now that all the files have been generated, the server can run the challenges,
setup the firewall and turn the VPN on.

> Notice: **the distribution of VPN certificates is out of scope**. However,
> inside this repository you can find a proof-of-concept [webserver](webserver)
> that uses Github to authenticate the users and distributes their Wireguard
> certificates
