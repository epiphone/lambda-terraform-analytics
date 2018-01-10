variable "analytics_consumer_username" {
  default = "consumer_dev"
}

variable "analytics_consumer_password" {}

variable "analytics_producer_username" {
  default = "producer_dev"
}

variable "analytics_producer_password" {}

variable "aws_region" {
  default = "eu-central-1"
}

variable "functions_rel_path" {
  default = "../../functions"
}
