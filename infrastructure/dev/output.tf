output "analytics_db_consumer_url" {
  sensitive = true
  value     = "${local.analytics_db_consumer_url}"
}

output "analytics_db_producer_url" {
  sensitive = true
  value     = "${local.analytics_db_producer_url}"
}

output "analytics_queue_url" {
  value = "${module.analytics_queue.queue_url}"
}

output "messaging_publisher_arn" {
  value = "${module.messaging.publisher_arn}"
}

output "messaging_topic_arn" {
  value = "${module.messaging.topic_arn}"
}
