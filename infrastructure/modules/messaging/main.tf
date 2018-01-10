variable "stage" {}

resource "aws_sns_topic" "event_created" {
  name = "event_created_${var.stage}"
}

resource "aws_iam_user" "publisher" {
  name = "event_publisher_${var.stage}"
}

resource "aws_sns_topic_policy" "publisher_policy" {
  arn = "${aws_sns_topic.event_created.arn}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Id": "event_created_sns_policy_${var.stage}",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "${aws_iam_user.publisher.arn}"
        ]
      },
      "Action": "SNS:Publish",
      "Resource": "${aws_sns_topic.event_created.arn}"
    }
  ]
}
EOF
}

output "publisher_arn" {
  value = "${aws_iam_user.publisher.arn}"
}

output "topic_arn" {
  value = "${aws_sns_topic.event_created.arn}"
}
