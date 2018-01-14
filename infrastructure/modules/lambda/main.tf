// Lambda IAM role base definition
resource "aws_iam_role" "role" {
  name = "lambda_${var.name}_${var.stage}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

// Logging and X-ray permissions:
resource "aws_iam_role_policy_attachment" "basic_execution_role" {
  role       = "${aws_iam_role.role.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "xray_write_only_access" {
  role       = "${aws_iam_role.role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
}

// Lambda zip archive
data "archive_file" "zip" {
  type        = "zip"
  source_dir  = "${var.functions_path}/${var.name}/build/"
  output_path = "${path.root}/.terraform/archive_files/${var.name}_lambda.zip"
}

resource "aws_lambda_function" "lambda" {
  function_name    = "${var.name}_${var.stage}"
  filename         = "${data.archive_file.zip.output_path}"
  source_code_hash = "${data.archive_file.zip.output_base64sha256}"
  role             = "${aws_iam_role.role.arn}"
  description      = "${var.description}"
  handler          = "${var.handler}"
  runtime          = "${var.runtime}"
  memory_size      = "${var.memory_size}"
  timeout          = "${var.timeout}"

  environment {
    variables = "${merge(var.environment, map(
      "STAGE", "${var.stage}"
    ))}"
  }
}

resource "aws_cloudwatch_event_rule" "scheduled" {
  count               = "${var.schedule != "" ? 1 : 0}"
  name                = "${var.name}_scheduled_event_${var.stage}"
  description         = "Trigger ${var.name}_${var.stage} as per ${var.schedule}"
  schedule_expression = "${var.schedule}"
}

resource "aws_cloudwatch_event_target" "scheduled_trigger" {
  count     = "${var.schedule != "" ? 1 : 0}"
  rule      = "${aws_cloudwatch_event_rule.scheduled.name}"
  target_id = "check_foo"
  arn       = "${aws_lambda_function.lambda.arn}"
}

resource "aws_lambda_permission" "allow_scheduled_trigger_to_invoke_lambda" {
  count         = "${var.schedule != "" ? 1 : 0}"
  statement_id  = "AllowExecutionFromCloudWatch_${var.name}_${var.stage}"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambda.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.scheduled.arn}"
}
