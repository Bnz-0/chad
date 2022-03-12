#!/usr/bin/env python3
import sys, os, ipaddress, shutil, re, random
import click
from utils import *


## options callbacks ##
def print_version(ctx, param, value):
	if value:
		print(f"{os.path.basename(__file__)} version: 0.0.1")
		sys.exit(0)

def colors_setter(ctx, param, value):
	Config.colors = value
	return value

## common options ##
click_colors = click.option("--colors/--no-colors",
	default=True, callback=colors_setter,
	help="Enable/disable the terminal colors"
)
def click_instance(required):
	return click.option("--instance-file", "-f",
		type=click.Path(exists=True), required=required,
		help="An instances file (format allowed: csv, json)"
	)
click_csv_delim = click.option("--csv-delimiter", "csv_delimiter",
	type=str, default=",", show_default=True,
	help="Delimiter for the csv file (used only if -f specifies a csv file)"
)
click_id = click.option("--id", "id_key",
	type=str, default="github_username", show_default=True,
	help="Key to use as identifier for each instance"
)
click_editor = click.option("--editor",
	envvar='EDITOR', type=str, default="nano",
	help="Editor use to edit a file"
)
click_edit = click.option("--edit/--no-edit",
	is_flag=True, default=True,
	help="Allows to edit a file"
)
def click_out(default):
	return click.option("-o", "--out",
		type=click.Path(), default=default, show_default=True,
		help="Output directory"
	)

## other constants ##
RE_B64 = "^(?:[A-Za-z\\d+/]{4})*(?:[A-Za-z\\d+/]{3}=|[A-Za-z\\d+/]{2}==)?$"



@click.group()
@click.option("--version", is_flag=True, callback=print_version)
def cli(version):
	pass



@cli.command()
@click.option("-n", type=int,
	default=1, show_default=True,
	help="Number of instances (used only if -f is not specified)"
)
@click_instance(required=False)
@click.option("--seed", type=int,
	default=None, show_default=False,
	help="Set the seed used by the pseudo-random functions"
)
@click_out("generated_challs")
@click.option("--force", is_flag=True,
	help="Ignore the eventual existence of a challenge in the output folder"
)
@click_colors
@click.option("--steps-folder", "steps_folder",
	type=str, default="steps", show_default=True,
	help="Path to the folder where to find the steps files"
)
@click_id
@click_csv_delim
@click.option("--docker-compose", is_flag=True,
	help="Concatenates all the 'docker-compose.yml' files in each generated challenge into a single file to deploy all the challenges at once"
)
@click.option("-p", "--param", type=str,
	multiple=True, callback=parse_param,
	help="Parameters aviable in the step files and templates (format must be key=value)"
)
@click.option("--verbose", is_flag=True)
@click.argument("challenge_dir", type=click.Path(exists=True))
@click.pass_context
def generate(ctx, n, instance_file, seed, out, force, colors, steps_folder, docker_compose, id_key, csv_delimiter, param, verbose, challenge_dir):
	if os.path.isdir(challenge_dir):
		Config.challenge_dir = challenge_dir
	else: # challs file
		challs = load_json(challenge_dir)
		if not isinstance(challs, list):
			challs = [challs]
		original_params = ctx.params.copy()
		for instance in challs:
			# adjust paths if necessary
			for path_args in ('challenge_dir', 'out', 'instance_file'):
				if path_args in instance:
					instance[path_args] = os.path.join(os.path.dirname(challenge_dir), instance[path_args])
			ctx.params = {**original_params, **instance}
			ctx.forward(generate)
		return

	Config.from_args(ctx.params)
	random.seed(seed)
	log(f"Config: {Config.to_str()}")
	log(f"Seed: {seed}")
	os.makedirs(Config.out, exist_ok=True)

	instances = Instance.load(instance_file, id_key, csv_delimiter) if instance_file else [Instance({id_key: str(i)}, id_key) for i in range(n)]
	for instance in instances:
		log(f"Running the instance {instance.id} ({challenge_dir})")
		if not instance.create_folder(force):
			print(f"{clr('Warning', fg='yellow')}: the challenge \"{clr(os.path.basename(challenge_dir), style='bold')}\" for the instance {clr(instance.id, style='bold')} already exists (use '--force' to recreate it)")
			continue
		chall_gen(instance, docker_compose)
		instance.cleanup()

	if docker_compose:
		dc_content = "version: \"3\"\nservices:\n"
		for instance in instances:
			with open(os.path.join(instance.out_path(), "docker-compose.yml"), 'r') as f:
				dc_content += f.read() + '\n'
		with open(os.path.join(out, "docker-compose.yml"), 'w+') as f:
			f.write(dc_content)


def chall_gen(instance, docker_compose):
	pwd = os.getcwd()
	os.chdir(instance.out_path())
	ctx = { **vars(context), **instance.entries, **Config.params }
	for i,ctx_file in enumerate(sorted(fname for fname in os.listdir(Config.steps_folder) if fname.endswith(".py"))):
		log(f"Running the step {ctx_file}")
		load_context(os.path.join(Config.steps_folder, ctx_file), ctx)
		if not ctx[CTX_FILES_OPT] or len(ctx[CTX_FILES_OPT]) == 0:
			log(f"No file found in {CTX_FILES_OPT}")
			continue
		ctx[CTX_FILES_OPT] = list(expand_paths(ctx[CTX_FILES_OPT]))
		if docker_compose and i==0:
			 # automatically adds the docker-compose.yml to the files to be processed
			ctx[CTX_FILES_OPT].append("docker-compose.yml")
		for file in ctx[CTX_FILES_OPT]:
			log(f"Processing {file}")
			apply_ctx(file, ctx)
	os.chdir(pwd)


def apply_ctx(file, ctx):
	env = Environment()
	def saveas(value, name):
		ctx[name] = value
		return value
	env.filters['saveas'] = saveas
	with open(file, 'r') as f:
		template = env.from_string(f.read())
	with open(file, 'w') as f:
		f.write(template.render(ctx))



@cli.command()
@click_editor
@click_edit
@click_colors
@click.option("--force",
	is_flag=True, default=False,
	help="Overwrite the CONF_FILE file if present"
)
@click.argument("conf_file", required=False)
def init(editor, edit, force, colors, conf_file):
	conf_file = conf_file or "conf.json"
	if os.path.exists(conf_file) and not force:
		print(f"{clr('Error:',fg='red')}: File \"{conf_file}\" already exists, use --force to overwrite it")
		return
	save_json(conf_file, {
		INTERFACE: "wg0",
		ENDPOINT: "127.0.0.1:5820",
		SUBNET: "10.20.30.0/24",
		PUB_KEY: "<server public key>",
		G_BASE_PORT: 5000,
		PORT_RANGE: 20,
		CERT_FOLDER: "wg_certificates",
		RULES_FOLDER: "iptable_rules",
		USER_DB_FILE: "user.json",
	})
	if edit: edit_file(editor, conf_file)



@cli.command()
@click_instance(required=True)
@click_csv_delim
@click_id
@click_edit
@click_editor
@click_colors
@click_out(".")
@click.option("--force", is_flag=True,
	help="Regenerates the wireguard config and ignores the already created certificates and iptabels ruels"
)
@click.argument("config_file", type=click.Path(exists=True))
def setup(instance_file, csv_delimiter, id_key, edit, editor, colors, out, force, config_file):
	conf = load_json(config_file)

	# folders creation
	for folder in filter(lambda f: f!="", [".", conf[CERT_FOLDER], conf[RULES_FOLDER]]):
		os.makedirs(os.path.join(out, folder), exist_ok=True) # if os.makedirs takes an empty string it raise an exception

	interface_file = os.path.join(out, f"{conf[INTERFACE]}.conf")
	if force or re.match(RE_B64, conf.get(PUB_KEY, "a")) is None:
		if force or prompt("It seems that the public key is missing, generate the interface conf?", True):
			priv_key, pub_key = wg_gen_keys()
			with open(os.open(interface_file, os.O_CREAT|os.O_WRONLY, 0o600), 'w+') as f:
				f.write(WG_INTERFACE_TEMPLATE.format(
					private_key = priv_key,
					address = conf[SUBNET].replace(".0/", ".1/"), # the server will have the x.y.z.1 ip
					listen_port = conf[ENDPOINT].split(':')[1],
				))
				f.truncate()
			conf[PUB_KEY] = pub_key
			save_json(config_file, conf) # updates the config file with the pubkey generated
		else:
			print(f"The setup cannot continue without the server public key.\nTry to run `wg showconf {conf[INTERFACE]}` to retrieve it")
			return

	if not os.path.exists(conf[USER_DB_FILE]):
		save_json(conf[USER_DB_FILE], list())
	db = load_json(conf[USER_DB_FILE])
	instance_users = remove_empty_id(load(instance_file, csv_delimiter), id_key)

	server_ip = str(ipaddress.ip_network(conf[SUBNET]).network_address + 1)

	# update the db
	db_len = 0 if force else len(db)
	for user in instance_users:
		i = -1
		try: i = next((i for i,u in enumerate(db) if u[id_key] == user[id_key]), -1)
		except KeyError: pass
		if i > -1:
			db[i].update(user)
		else:
			# add network props to the user
			user[IP] = str(ipaddress.ip_network(conf[SUBNET]).network_address + len(db) + 2)
			user[BASE_PORT] = conf[PORT_RANGE]*len(db) + conf[G_BASE_PORT]
			db.append(user)


	# edit the database if needed
	save_json(conf[USER_DB_FILE], db)
	while edit and prompt("Edit the user database?", True):
		try:
			db = edit_file(editor, conf[USER_DB_FILE])
			break
		except Exception as e:
			print(clr("Error:",fg='red'), e)

	# for each new user create his config using the updated db
	for i in range(db_len, len(db)):
		user = db[i]
		# generate wireguard configs
		priv_key, pub_key = wg_gen_keys()
		user_ip = user[IP]+"/32"
		with open(interface_file, 'a+') as f:
			f.write(WG_PEER_TEMPLATE.format(
				public_key = pub_key,
				allowed_ips = user_ip
			))
		wg_cert_filename = f"{user[id_key]}.conf"
		with open(os.path.join(out, conf[CERT_FOLDER], wg_cert_filename), 'w+') as f:
			f.write(WG_CLIENT_TEMPLATE.format(
				private_key = priv_key,
				address = user_ip,
				public_key = conf[PUB_KEY],
				endpoint = conf[ENDPOINT],
				subnet = conf[SUBNET],
                filename = wg_cert_filename,
                name = user['name'],
                gh_username = user['github_username'],
                ip_address = user['ip'],
                base_port = user['base_port'],
                identifier = user['identifier']
			))
		# generate iptables rules
		port_range = f"{user[BASE_PORT]}:{user[BASE_PORT]+conf[PORT_RANGE]-1}"
		for act, prefix in (("-I", "enable"), ("-D", "disable")):
			with open(os.path.join(out, conf[RULES_FOLDER], f"{prefix}_{user[id_key]}.sh"), 'w+') as f:
				f.write(IPT_SCRIPT_TEMPLATE.format(
					act = act,
					ip = user[IP],
					port_range = port_range,
                    server_ip = server_ip
				))
		print(f"Generated configs for {clr(user[id_key], style='bold')}")

if __name__ == "__main__":
	cli()
