#!/bin/env python3
import os, json
from flask import Flask, request, send_from_directory, render_template, abort, redirect
import requests as req

client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
page_title = os.environ['page_title']
homepage = os.environ['homepage']

webserver = Flask(__name__, template_folder=os.getcwd())

@webserver.route("/")
def root():
	return render_template('index.html',
		title =  page_title,
		oauth_url =  f"https://github.com/login/oauth/authorize?client_id={client_id}",
	)

@webserver.route("/cert")
def cert():
	code = request.args.get('code', None)
	if code is None:
		abort(400) # bad request

	try:
		res = req.post("https://github.com/login/oauth/access_token",
			headers = {
				'Accept': "application/json"
			},
			data = {
				'client_id': client_id,
				'client_secret': client_secret,
				'code': code,
			},
		)
		res.raise_for_status()

		auth_token = json.loads(res.text)['access_token']
		res = req.get("https://api.github.com/user",
			headers = {
				'Authorization': f"token {auth_token}"
			}
		)
		res.raise_for_status()

		return send_from_directory(
			'/wg_certificates',
			json.loads(res.text)['login'] + ".conf",
			as_attachment=True,
		)
	except:
		return redirect(homepage)

webserver.run(host="0.0.0.0", port=5000, debug=False)
