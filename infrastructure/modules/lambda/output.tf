output "arn" {
  value = "${aws_lambda_function.lambda.arn}"
}

output "iam_role_name" {
  value = "${aws_iam_role.role.name}"
}
