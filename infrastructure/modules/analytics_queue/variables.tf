variable "analytics_db_url" {}
variable "analytics_db_table" {}
variable "event_created_topic_arn" {}
variable "functions_path" {}
variable "stage" {}

variable "consumer_schedule" {
  default     = "rate(5 minutes)"
  description = "Schedule expression for the Cloudwatch cron event that triggers the consumer Lambda."
}
