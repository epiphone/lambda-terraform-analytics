variable "stage" {}
variable "producer_username" {}
variable "producer_password" {}
variable "consumer_username" {}
variable "consumer_password" {}

resource "postgresql_role" "producer" {
  name     = "${var.producer_username}"
  login    = true
  password = "${var.producer_password}"
}

resource "postgresql_role" "consumer" {
  name     = "${var.consumer_username}"
  login    = true
  password = "${var.consumer_password}"
}

resource "postgresql_schema" "schema" {
  name = "analytics_${var.stage}"

  policy {
    usage = true
    role  = "${postgresql_role.producer.name}"
  }

  policy {
    usage = true
    role  = "${postgresql_role.consumer.name}"
  }
}

output "schema" {
  value = "${postgresql_schema.schema.name}"
}
