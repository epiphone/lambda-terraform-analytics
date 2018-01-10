variable "analytics_db_url" {}
variable "analytics_db_table" {}
variable "event_created_topic_arn" {}
variable "functions_path" {}
variable "stage" {}

resource "aws_sqs_queue" "deadletter" {
  name = "analytics_events_deadletter_${var.stage}"
}

resource "aws_sqs_queue" "events" {
  name           = "analytics_events_${var.stage}"
  redrive_policy = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.deadletter.arn}\",\"maxReceiveCount\":2}"
}

resource "aws_sns_topic_subscription" "on_event_created" {
  topic_arn = "${var.event_created_topic_arn}"
  protocol  = "sqs"
  endpoint  = "${aws_sqs_queue.events.arn}"
}

resource "aws_sqs_queue_policy" "queue_policy" {
  queue_url = "${aws_sqs_queue.events.id}"

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "analytics_events_queue_${var.stage}",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "SQS:SendMessage",
      "Resource": "${aws_sqs_queue.events.arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${var.event_created_topic_arn}"
        }
      }
    }
  ]
}
POLICY
}

module "consumer_lambda" {
  source = "../lambda"

  name           = "analytics_consumer"
  description    = "Consume analytics events queue."
  functions_path = "${var.functions_path}"
  timeout        = 300
  stage          = "${var.stage}"

  environment = {
    SQS_URL           = "${aws_sqs_queue.events.id}"
    WORKER_LAMBDA_ARN = "${module.worker_lambda.arn}"
  }
}

module "worker_lambda" {
  source = "../lambda"

  name           = "analytics_worker"
  description    = "Store analytics events into database."
  functions_path = "${var.functions_path}"
  timeout        = 5
  stage          = "${var.stage}"

  environment = {
    DB_URL     = "${var.analytics_db_url}"
    TABLE_NAME = "${var.analytics_db_table}"
  }
}

// SQS permissions for consumer IAM role
resource "aws_iam_role_policy" "consumer" {
  name = "analytics_consumer_sqs_rd_${var.stage}"
  role = "${module.consumer_lambda.iam_role_name}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "sqs:DeleteMessage",
        "sqs:DeleteMessageBatch",
        "sqs:ReceiveMessage"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sqs_queue.events.arn}"
    },
    {
      "Action": [
        "lambda:InvokeAsync",
        "lambda:InvokeFunction"
      ],
      "Effect": "Allow",
      "Resource": "${module.worker_lambda.arn}"
    }
  ]
}
EOF
}

output "queue_url" {
  value = "${aws_sqs_queue.events.id}"
}
