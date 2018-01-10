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

variable "timeout" {
  default = "3"
}

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

output "arn" {
  value = "${aws_lambda_function.lambda.arn}"
}

output "iam_role_name" {
  value = "${aws_iam_role.role.name}"
}
