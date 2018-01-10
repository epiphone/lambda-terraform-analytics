output "database_url" {
  sensitive = true
  value     = "postgres://${var.analytics_db_master_username}:${var.analytics_db_master_password}@${aws_db_instance.shared_analytics_db.address}:${aws_db_instance.shared_analytics_db.port}/${aws_db_instance.shared_analytics_db.name}"
}

output "analytics_db_username" {
  value = "${var.analytics_db_master_username}"
}

output "analytics_db_password" {
  sensitive = true
  value     = "${var.analytics_db_master_password}"
}

output "analytics_db_address" {
  value = "${aws_db_instance.shared_analytics_db.address}"
}

output "analytics_db_port" {
  value = "${aws_db_instance.shared_analytics_db.port}"
}

output "analytics_db_name" {
  value = "${aws_db_instance.shared_analytics_db.name}"
}
