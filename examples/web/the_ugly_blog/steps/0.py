import hashlib, requests, json
from urllib.parse import urlencode
_files = ['*.sql', '*.php', '*.sh']

is_passwd_plain = bool(rand_int(0,1))

def md5(s):
	if is_passwd_plain:
		return s
	return hashlib.md5(bytes(s, 'utf-8')).hexdigest()

def rand_quote():
	print("Requesting random quote... ", end='')
	res = requests.get('https://api.quotable.io/random')
	if res.status_code == 200:
		try:
			quote = json.loads(res.text)['content']
			print(quote)
			return quote
		except: raise Exception("rand_quote error")
	raise Exception("rand_quote error")

# names taken from https://www.ssa.gov/OACT/babynames/decades/century.html
_names = ['James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','William','Elizabeth','David','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Charles','Karen','Christopher','Nancy','Daniel','Lisa','Matthew','Betty','Anthony','Margaret','Mark','Sandra','Donald','Ashley','Steven','Kimberly','Paul','Emily','Andrew','Donna','Joshua','Michelle','Kenneth','Dorothy','Kevin','Carol','Brian','Amanda','George','Melissa','Edward','Deborah','Ronald','Stephanie','Timothy','Rebecca','Jason','Sharon','Jeffrey','Laura','Ryan','Cynthia','Jacob','Kathleen','Gary','Amy','Nicholas','Shirley','Eric','Angela','Jonathan','Helen','Stephen','Anna','Larry','Brenda','Justin','Pamela','Scott','Nicole','Brandon','Emma','Benjamin','Samantha','Samuel','Katherine','Gregory','Christine','Frank','Debra','Alexander','Rachel','Raymond','Catherine','Patrick','Carolyn','Jack','Janet','Dennis','Ruth','Jerry','Maria']

# list of most common password (source: https://en.wikipedia.org/wiki/List_of_the_most_common_passwords)
_common_password = ['123456','123456789','qwerty','password','1111111','12345678','abc123','1234567','password1','12345','1234567890','123123','000000','Iloveyou','1234','1q2w3e4r5t','Qwertyuiop','123','Monkey','Dragon']

# create the users
n_user = rand_int(20, len(_names))
users = [remove_one(_names) for _ in range(n_user)]

# select one randomly to be the admin
admin_index = rand_int(0, len(users)-1)
admin = users[admin_index]
admin_password = choose_one(_common_password)

flag = f"FLAG:{rand_str(20)}"
