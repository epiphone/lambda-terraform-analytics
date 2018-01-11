locals {
  analytics_db_consumer_url = "postgres://${var.analytics_consumer_username}:${var.analytics_consumer_password}@${data.terraform_remote_state.shared.analytics_db_address}:${data.terraform_remote_state.shared.analytics_db_port}/${data.terraform_remote_state.shared.analytics_db_name}"
  analytics_db_producer_url = "postgres://${var.analytics_producer_username}:${var.analytics_producer_password}@${data.terraform_remote_state.shared.analytics_db_address}:${data.terraform_remote_state.shared.analytics_db_port}/${data.terraform_remote_state.shared.analytics_db_name}"
  stage                     = "staging"
}

terraform {
  backend "s3" {
    encrypt = true
    key     = "terraform-staging.tfstate"
    region  = "eu-central-1"
  }
}

provider "aws" {
  region = "${var.aws_region}"
}

provider "postgresql" {
  host            = "${data.terraform_remote_state.shared.analytics_db_address}"
  port            = "${data.terraform_remote_state.shared.analytics_db_port}"
  database        = "${data.terraform_remote_state.shared.analytics_db_name}"
  username        = "${data.terraform_remote_state.shared.analytics_db_username}"
  password        = "${data.terraform_remote_state.shared.analytics_db_password}"
  connect_timeout = 15
}

data "terraform_remote_state" "shared" {
  backend = "s3"

  config {
    bucket  = "${var.terraform_state_bucket_name}"
    region  = "eu-central-1"
    key     = "terraform-shared.tfstate"
    encrypt = true
  }
}

module "messaging" {
  source = "../modules/messaging"

  stage = "${local.stage}"
}

module "analytics_queue" {
  source = "../modules/analytics_queue"

  functions_path          = "${path.module}/${var.functions_rel_path}"
  stage                   = "${local.stage}"
  event_created_topic_arn = "${module.messaging.topic_arn}"
  analytics_db_url        = "${local.analytics_db_producer_url}"
  analytics_db_table      = "${module.analytics_db.schema}.events"
}

module "analytics_db" {
  source = "../modules/analytics_db"

  stage             = "${local.stage}"
  consumer_username = "${var.analytics_consumer_username}"
  consumer_password = "${var.analytics_consumer_password}"
  producer_username = "${var.analytics_producer_username}"
  producer_password = "${var.analytics_producer_password}"
}
