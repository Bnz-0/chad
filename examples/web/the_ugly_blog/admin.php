<?php
session_start();

if(isset($_SESSION["is_admin"]) && $_SESSION["is_admin"]) {
	print("{{ flag }}");
} else {
	print("Unauthorized");
}

?>
