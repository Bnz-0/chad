CREATE TABLE Users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE,
	password TEXT,
	is_admin INT DEFAULT 0
);

{% for i in range(n_user) %}
INSERT INTO Users (username, password) VALUES ('{{ users[i] }}', '{{ md5(rand_str(5,20)) }}');
{% endfor %}

UPDATE Users SET is_admin=1, password='{{ md5(admin_password) }}' WHERE username='{{ admin }}';

