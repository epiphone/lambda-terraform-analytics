output "queue_url" {
  value = "${aws_sqs_queue.events.id}"
}
