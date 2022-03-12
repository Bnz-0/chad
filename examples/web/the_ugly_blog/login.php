<?php
session_start();

$db = new SQLite3("database.sqlite");

if(!$db) {
	echo "DB error";
} else {
{% if is_passwd_plain %}
	$username = SQLite3::escapeString($_GET["username"]);
	$password = $_GET["password"];
{% else %}
	$username = $_GET["username"];
	$password = md5($_GET["password"]);
{% endif %}

{% if bool(rand_int(0,1)) %}
	$sql = "SELECT username,is_admin FROM Users WHERE username='" . $username . "' AND password='" . $password . "'";
{% else %}
	$sql = "SELECT username,is_admin FROM Users WHERE password='" . $password . "' AND username='" . $username . "'";
{% endif %}

	$res = $db->query($sql);
	if($res->numColumns() && $res->columnType(0) != SQLITE3_NULL) {
		$user = $res->fetchArray();
		if($user) {
			$_SESSION["username"] = $user["username"];
			$_SESSION["is_admin"] = $user["is_admin"] == 1;
		}
	}
}

header("Location: /index.php");
?>
