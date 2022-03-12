import sys, os, json, csv, subprocess as subp, ipaddress, re
from shutil import copytree, rmtree
from glob import glob
import click, colors
from jinja2 import Environment
import context


## instance's config keys ##
INTERFACE = 'interface' # used to check if the interface already exists
ENDPOINT = 'endpoint' # address:port
SUBNET = 'subnet' # interface subnet
PUB_KEY = 'pubkey' # pubkey of the interface
G_BASE_PORT = 'base_port' # global base port
PORT_RANGE = 'port_range' # how many port a user can have
# Folders/Files
CERT_FOLDER = 'cert_folder' # where to put/find the user's certificates
RULES_FOLDER = 'rules_folder' # where to put/find the user's iptable rules
USER_DB_FILE = 'user_database' # path to the user database json file

## user DB keys ##
IP = 'ip'
BASE_PORT = 'base_port'

## HTML temlpate key ##
TITLE = 'title'
OAUTH_URL = 'oauth_url'

## other constants ##
CTX_FILES_OPT = '_files'


###############################################################################
# Generic utils
###############################################################################

class Config:
	challenge_dir = None
	steps_folder = None
	out = None
	colors = None
	params = None
	verbose = None

	@staticmethod
	def from_args(args):
		# needed only by the generator command
		Config.challenge_dir = args['challenge_dir']
		Config.steps_folder = args['steps_folder']
		Config.out = args['out']
		Config.colors = args['colors']
		Config.params = args['param']
		Config.verbose = args['verbose']

	@staticmethod
	def to_str():
		return f"challenge_dir={Config.challenge_dir}, steps_folder={Config.steps_folder}, out={Config.out}, colors={Config.colors}, params={Config.params}, verbose={Config.verbose}"


def clr(s, *args, **kwargs):
	return colors.color(s, *args, **kwargs) if Config.colors else s

def log(s):
	if Config.verbose:
		print(s)


###############################################################################
# File utils
###############################################################################

def load_json(filename):
	with open(filename, 'r') as f:
		return json.load(f)

def save_json(filename, data):
	with open(filename, 'w+') as f:
		json.dump(data, f, indent='\t')

def load_csv(filename, csv_delimiter=','):
	with open(filename, 'r') as f:
		return list(csv.DictReader(f, delimiter=csv_delimiter))

def save_csv(filename, data, csv_delimiter=','):
	fields = set()
	for d in data:
		fields |= set(d.keys())
	with open(filename, mode='w+') as f:
		writer = csv.DictWriter(
			f,
			fieldnames=fields,
			delimiter=csv_delimiter
		)
		writer.writeheader()
		for row in data:
			writer.writerow(row)

def load(filename, *args, **kwargs):
	ext = filename[filename.rfind('.')+1:].lower()
	if ext == 'csv':
		return load_csv(filename, *args, **kwargs)
	elif ext == 'json':
		return load_json(filename)
	with open(filename, 'r') as f:
		return  f.read()

def save(filename, data, *args, **kwargs):
	ext = filename[filename.rfind('.')+1:].lower()
	if ext == 'csv':
		return save_csv(filename, data, *args, **kwargs)
	elif ext == 'json':
		return save_json(filename, data)
	with open(filename, 'w+') as f:
		return  f.write(data)


def remove_empty_id(data, key):
	def filter_and_wanr(d):
		if d[key].strip() == "":
			print(f"{clr('Warning', fg='yellow')}: found empty {key} in {d}")
			return False
		return True
	return filter(filter_and_wanr, data)


###############################################################################
# generator utils
###############################################################################

def expand_paths(paths):
	if isinstance(paths, str):
		paths = [paths]
	paths_expanded = set()
	for path in paths:
		paths_expanded |= set(glob(path, recursive=True))
	return paths_expanded

class Instance:
	@staticmethod
	def load(file_path, id_key, csv_delimiter):
		ext = file_path[file_path.rfind('.')+1:].lower()
		if ext == 'csv':
			import csv
			with open(file_path, 'r') as f:
				instances = list(csv.DictReader(f, delimiter=csv_delimiter))
		elif ext == 'json':
			import json
			with open(file_path, 'r') as f:
				instances = json.load(f)
		else:
			print("Instances file format not supported", file=sys.stderr)
			sys.exit(1)

		instances = remove_empty_id(instances, id_key)
		return [Instance(instance, id_key) for instance in instances]


	def __init__(self, entries, id_key):
		self.entries = entries
		self.id = entries[id_key]

	def __getitem__(self, k):
		return self.entries[k]

	def out_path(self):
		return os.path.join(Config.out, self.id)

	def create_folder(self, force=False):
		if not force and os.path.exists(self.out_path()):
			return False
		copytree(Config.challenge_dir, self.out_path(), dirs_exist_ok=True)
		return True

	def cleanup(self):
		rmtree(os.path.join(self.out_path(), Config.steps_folder))


def load_context(path, ctx):
	ctx[CTX_FILES_OPT] = None
	exec_ctx = vars(context)
	exec_ctx.update(ctx)
	exec_ctx['Config'] = Config
	exec_ctx['clr'] = clr
	exec_ctx['log'] = log
	exec_ctx['expand_paths'] = expand_paths
	with open(path, 'r') as f:
		exec(f.read(), exec_ctx)
	ctx.update(exec_ctx)

def parse_param(ctx, param, value):
	params = {}
	for v in value:
		match = re.match("^([^=]+)=(.+)$", v)
		if match is None:
			raise click.BadParameter(f"format must be key=value (wrong parameter: '{v}')")
		params[match[1]] = match[2]
	return params


###############################################################################
# setup utils
###############################################################################

def edit_file(editor, filename):
	ret_code = subp.call(f"{editor} {filename}", shell=True)
	if ret_code != 0:
		sys.exit(ret_code)
	return load(filename)

def prompt(msg, default):
	msg = msg + (" [Y/n] " if default else " [y/N] ")
	while True:
		resp = input(msg)
		if resp == "":
			return default
		if resp.lower() == "y":
			return True
		if resp.lower() == "n":
			return False

def run_cmd(cmd, input=None):
	res = subp.run(cmd, check=True, capture_output=True, input=input, text=True)
	return res.stdout

def wg_gen_keys():
	priv_key = run_cmd(["wg", "genkey"]).strip('\n')
	pub_key = run_cmd(["wg", "pubkey"], priv_key).strip('\n')
	return priv_key, pub_key

def subnet_mask(net):
	net = str(net)
	return net[net.rfind('/'):]

###############################################################################
# Templates
###############################################################################

WG_INTERFACE_TEMPLATE = """[Interface]
PrivateKey = {private_key}
Address = {address}
ListenPort = {listen_port}

"""

WG_PEER_TEMPLATE = """[Peer]
PublicKey = {public_key}
AllowedIPs = {allowed_ips}

"""

WG_CLIENT_TEMPLATE = """#
# This WireGuard configuration file belongs to "{identifier}"
# GitHub username: {gh_username}
#  VPN IP Address: {ip_address}
#       Base port: {base_port}
#
# BEWARE: do not change anything in this configuration file
# (your public-key, specified below, is already associated with your
#  IP-address on the server; other keys/IP-addresses will not work)
#
# To install WireGuard see: https://www.wireguard.com/install
# Then, to activate your VPN, run:
# $ sudo wg-quick up ./{filename}
#
# The above command creates a network interface named {gh_username}; rename
# your ".conf" file if you prefer to use a different interface name
#
# To deactivate the VPN, run:
# $ sudo wg-quick down ./{filename}
#

# Your client configuration:
[Interface]
PrivateKey = {private_key}
Address = {address}

# Server configuration:
[Peer]
PublicKey = {public_key}
Endpoint = {endpoint}
AllowedIPs = {subnet}
"""

IPT_SCRIPT_TEMPLATE = """#!/bin/sh
iptables {act} DOCKER-USER -s {ip}        -m conntrack '!' --ctorigdst     {server_ip}  -j DROP
iptables {act} DOCKER-USER -s {ip} -p udp -m conntrack '!' --ctorigdstport {port_range} -j DROP
iptables {act} DOCKER-USER -s {ip} -p tcp -m conntrack '!' --ctorigdstport {port_range} -j DROP
"""

DOCKER_SERVICE_TEMPLATE = """  {name}:
    build: ./{path}
    ports:
      - "{exposed_port}:{internal_port}"
"""
