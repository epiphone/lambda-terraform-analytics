# Analytics events handler

Store queued analytics events to Postgres.

AWs infra is defined in `main.tf` for reproducability.

## Dependencies

- aws-cli (and logged in user)
- [apex](https://github.com/apex/apex)
- [invoke](docs.pyinvoke.org/)
- pip-env >= 8.3.0
- terraform

## Install

Install dependencies:

```bash
pipenv install -d
```

## Deploy

First [assign secret terraform variables](https://www.terraform.io/intro/getting-started/variables.html#assigning-variables), for example by creating a `terraform.tfvars` file. Check `variables.tf` for required keys.

Then zip up the lambda with dependencies and apply terraform to set up all AWS resources:

```bash
inv build package # package lambda and dependencies into a .zip file
terraform apply
```

## Invoke

Invoke the deployed function:

```bash
aws lambda invoke --function-name=analytics_lambda --invocation-type=RequestResponse --payload='{"test": "value"}' --log-type=Tail output.txt
```

## Develop

Run `inv update` to quickly package and upload a new lambda zip without rebuilding dependencies.

### Local development

Use [SAM Local](https://github.com/awslabs/aws-sam-local) to invoke the lambda locally:

```bash
sam local invoke -e event.json
```

Local invocation is based on the `lambda/template.yaml` SAM template. `lambda/event.json` can be used as a test event. **Note**, don't use `sam local` for deployment as that's handled by `terraform` as outlined above.

## Access DB

Admin user db access:

```bash
inv psql
```

## Sample event

```json
{"event_id": "1234-asdf", "event_timestamp": "2017-12-20T17:29:36.272Z", "event_type": "test_event", "event_version": "1.0", "app_title": "main", "app_version": "1.0", "user_id": "someuser", "user_name": "test@user.com", "meta": {"x": [12]}, "user_payload": {"email": "test@user.com"}}
```
