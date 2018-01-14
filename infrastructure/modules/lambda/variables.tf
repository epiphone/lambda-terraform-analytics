variable "environment" {
  type    = "map"
  default = {}
}

variable "functions_path" {}
variable "name" {}
variable "stage" {}

variable "description" {
  default = "Created by Terraform"
}

variable "handler" {
  default = "main.main"
}

variable "runtime" {
  default = "python3.6"
}

variable "memory_size" {
  default = "128"
}

variable "schedule" {
  default     = ""
  description = "Schedule expression for optional Cloudwatch cron event that triggers Lambda."
}

variable "timeout" {
  default = "3"
}
