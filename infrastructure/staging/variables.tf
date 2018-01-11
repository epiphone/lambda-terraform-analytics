variable "analytics_consumer_username" {
  default = "consumer_staging"
}

variable "analytics_consumer_password" {}

variable "analytics_producer_username" {
  default = "producer_staging"
}

variable "analytics_producer_password" {}

variable "aws_region" {
  default = "eu-central-1"
}

variable "functions_rel_path" {
  default = "../../functions"
}

variable "terraform_state_bucket_name" {
  default = "lambda-terraform-analytics"
}
