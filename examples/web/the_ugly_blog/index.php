<?php
session_start();
?>
<html>
	<head>
		<title> The ugly blog </title>
		<style>
			.post {
				border: solid 1px;
				margin: 10px;
			}
			.author {
				font-size: small;
				font-style: italic;
			}
		</style>
	</head>
	<body>
		<h1> The ugly blog </h1>

		<?php
			if(isset($_SESSION["username"])) {
				print("<p> Welcome back " . $_SESSION["username"] . " </p>");
			}
			if(isset($_SESSION["is_admin"])) {
				print("<a href='/admin.php'> admin page </a>");
			}
		?>

		{% for i in range(rand_int(3,10)) %}
			<div class="post">
				<p> {{ rand_quote() }} </p>
				<p class="author"> Author: {{ users[rand_int(0,n_user-1)] }} </p>
			</div>
		{% endfor %}

		<div class="post">
			<p> The administrator of the blog wish you all a merry christmas and a happy new year! </p>
			<p class="author"> Author: {{ admin }} </p>
		</div>

		{% for i in range(rand_int(3,10)) %}
			<div class="post">
				<p> {{ rand_quote() }} </p>
				<p class="author"> Author: {{ users[rand_int(0,n_user-1)] }} </p>
			</div>
		{% endfor %}

		<br><br><br>
		<p> Login to make a post: </p>
		<form action="/login.php">
			 <label for="username">Username:</label><br>
			 <input type="text" id="username" name="username"><br>
			 <label for="password">Password:</label><br>
			 <input type="password" id="password" name="password"><br><br>
			 <input type="submit" value="Submit">
		</form>

	</body>
</html>
