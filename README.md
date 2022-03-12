# chad.py — CHallenge Automation and Deployment

**Chad** is a cli tool born from the necessity to generate multiple CTF-like challenges, each one similar but different, from a template for educational purposes.


## Installation
```bash
# clone the repo
git clone https://github.com/Bnz-0/chad.git
cd chad

# optional but strongly suggested, create a virtual environment
python -m venv .venv
source .venv/bin/activate

# install the requirements & enjoy
pip install -r requirements.txt
./chad.py --help
```

## Challenges generation

> TL;DR
>
> See an [example](examples) and the [command line interface](#command-line-interface).

To generate multiple different challenges, **chad** starts from a _challenge template_, which is simply a folder that can contains [any kind of file](#rendered-files) necessary to the final challenge, and the [_steps_ subfolder](#steps).
To generate a challenge from the template, **chad** first copy the whole content of the folder in the destination, then step-by-step it renders the files specified in the [_step scripts_](#steps) with [Jinja](https://jinja.palletsprojects.com/en/3.0.x/).

It iterates this process as many time as needed to generate _N_ different challenges. The success and the level of differences between two generated challenges depends totally by the user: the more random values he put, the more differences he will have.


### Rendered files
Any file in the template folder will be rendered using the [Jinja](https://jinja.palletsprojects.com/en/3.0.x/) template engine, this grants a lot of flexibility while we generate the file which will compose a final challenge.

In the Jinja template (i.e. any file in the _challenge template folder_) you can use any variables declared in the _step scripts_, and a series of utility built-in functions that you can find in [context.py](context.py).

Those utility functions are useful to randomize stuff around the challenge template, for example a buffer dimension or a particular value:
```c
char buf[{{ rand_int(100, 200) }}];
int x = {{ choose_one(hexspeak) }};
```
Which may generate this code:
```c
char buf[123];
int x = 0xc0ffe;
```
There are also specific functions that cover some annoying problem, for example generating a random value that can be passed to a `scanf`:
```c
int magicNumber = {{ rand_scanf_safe_int() }};
scanf("%s", buffer);
if(*(int*)buffer == magicNumber) puts("You won!");
```

> Useful references:
> - [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/)
> - [Utility built-in functions](context.py)


### Steps
In the _steps_ subfolder there are one or more _step script_, which are simply python script that will be evaluated by **chad** in **alphabetical order**.
Those scripts are used to force an order on the rendering of the other files, and also to give much more flexibility in the generation process.

So, with a _steps_ folder with this 3 files:
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


To specify which files to render, **chad** will search for a special optional variable: `_files`, which is a list containing all the files you want to render for that step.
For example:
```python
_files = ["challenge.c", "flag.txt"]
```
Or maybe something like that:
```python
_files = ["*.php", "some_folder/*.sql"]
```
If this variable in not present his default value is an empty list, which means that for that step no file will be rendered.

> How have an order could be useful? Sometimes the challenge you want to create needs to render different files in different times, or what you want is cannot achieved by just render some files. See [Test the generated challenges](#test-the-generated-challenges) for an example.

A _step script_ serves not only to force a rendering order. Any variable that you declare in those python script, will be available in the other file inside the template folder.
To be more specific, when you declare a variable, it will be available in the current step and in the future steps, but not in the steps already evaluated.

For example, if in the `1.py` step there is declared a variable `x = 42`, it is possible to use that variable in the step file `2.py` and in any files to rendered specified by the steps `1.py` and `2.py`.

In this way is it possible to reuse the variables generated in the previous step also in the next ones.

**Notice: those script are `eval()`uated by chad! This means that the code inside will be executed without any restriction.**


### Command line interface
Once a template is ready, generating the challenges is pretty simple. The `generate` subcommand support various arguments (see `./chad.py generate --help`), but ony 2 are needed to generate some challenges: the number of challenges and the path to the template.

For example this command will generate 5 challenges from the [`bomb`](examples/linux/bomb) template, and store the results in the `challs` folder:
```sh
./chad.py generate -n5 examples/linux/bomb -o challs
```
Alternatively with `-f`, we can use an _instances_ file, which should specify the challengers that will have to solve the generated challenges:
```sh
./chad.py generate -f examples/instances.csv examples/linux/bomb -o challs
```

> Notice: **any value of an instance file will be available as well in the templates**.
>
> For example it is possible to use the `{{github_username}}` variable since in the [instances.csv](examples/instances.csv) there is the "github_username" column for each instance.

Now, in the `challs` folder there are the generated challenges. Take a look of what **chad** generated.

### Test the generated challenges
A huge problem generating multiple challenges from a template is that some of them could be not solvable.
Independently from the reason, it is not a good idea to manually test one by one each generated challenge. A possible way to automate the test is to use the _steps_ system.

It is a good practice to generate not only the challenge, but also a script to solve it.
Doing this we can use the last _step_ to run it and see if it actually solve the generated challenge, so to automate also the testing phase and discard the unsolvable ones.

For instance, in the [bomb](examples/linux/bomb) example there are 3 steps.
The first two are for generating the source code, both for the challenge itself and for the `sol.py` file, which is the script that should be able to solve the challenge.
Then a third one ([`2.py`](examples/linux/bomb/steps/2.py)) which compile the source code and run the `sol.py` script to check the solution:
```python
import os
os.system("make")
check_solution("python sol.py", flag)
```
The `flag` variable was declared in a previous _step_ ([`0.py`](examples/linux/bomb/steps/0.py)), `check_solution` is just a function (from the [utilities](context.py)) that runs a command and checks for the flag.


## Deployment
**Chad** can also try to automate the deployment phase. It is not mandatory of course, but it is really useful when, for reasons, there is the necessity to expose the challenges trough a remote server instead send to each one the generated files.

There are countless ways to deploy a challenge, **chad** uses a mix of docker container, vpn and firewall rules. The idea is:
- Reach challenge will live inside a container
- To manage the user, everything will stand behind a vpn such that:
	- Each challenge will have a known port
	- Each user will have a known ip address inside the vpn (so a personal certificate for each user)
	- Each user will be able to see only his challenges (some firewall rules are needed to do this)

The preparation of the files needed to create a server that can deploy the generated challenges can be generated via **chad**.

> The requirements for the server are: [docker](https://www.docker.com/), [wireguard](https://www.wireguard.com/) as vpn and [iptables](https://git.netfilter.org/iptables/) as firewall.
>
> **Since chad only generate the configuration files, those requirements are needed only on the server**

First we need to put a _piece_ of docker-compose file in the challenge template(s) (see the [bomb one](examples/linux/bomb/docker-compose.yml) to have an example). This pieces will be merged in a final `docker-compose.yml` file that allows to run all the generated challenges at once.

Then we can create the file needed to run the server:
```sh
mkdir server
cd server
../chad.py init
```
`init` will initialize the configuration json, needed to generate all the the files.
The settings are:
- **interface**: the name of the wireguard interface
- **endpoint**: the endpoint of the vpn
- **subnet**: the subnet of the vpn
- **pubkey**: the public key of the vpn server (if it is not valid, **chad** will ask you if you want to to generate it)
- **base_port**: the starting port where expose the challenges
- **port_range**: how many port reserve for each user
- **cert_folder**: the folder where to place the certificates
- **rules_folder**: the folder where to place the scripts for iptables
- **user_database**: the name of the file that will be used to take trace of all the instances and their ports, ip and others

After that it will be possible to use the `setup` command:
```sh
../chad.py setup -f ../examples/instances.csv conf.json
```
It will initialize all the necessary files, but to work in needs the `conf.json` file (created by the `init` command), and an instance file, where to take all the users to include in the vpn.

> It is possible to run `setup` again with another instances file, it will add the users that are not already present.

At this point it is possible to generate the challenges **using the "user_database" file** generated by **chad** as instances:
```sh
cd ..
./chad.py generate -f server/user.json --docker-compose --param port_offset=0 examples/linux/bomb -o server/challs
```
`--docker-compose` is telling **chad** to concatenate the docker-compose files, and `--param port_offset=0` is adding a variable that we are using inside the docker-compose to decide which port use for this challenge.

This will works also with multiple templates, but from the command line it would be a nightmare. Instead passing the folder of the template, it is possible to use a json file to specify all the templates we want to generate. See [challs.json](examples/challs.json).

Now all the files needed are generated and the server can run the challenges, setup the firewall and turn on the vpn.

> Notice: **the distribution of the vpn certificates is out of scope**. Inside this repository you can find a possible [webserver](webserver) that uses github to authenticate the users and grant the vpn access.
