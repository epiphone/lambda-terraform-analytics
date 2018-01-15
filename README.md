# Simple Lambda/Terraform analytics service

Sets up A) a general messaging topic in which to hook up additional event listeners and B) a little analytics service that feeds all events into a database. The database can be further plugged into a dashboard frontend like [Superset](https://github.com/apache/incubator-superset) or [Metadash](https://github.com/metabase/metabase).

Features include
- Terraform-managed Lambdas (inspired by [this blog post](https://medium.com/build-acl/aws-lambda-deployment-with-terraform-24d36cc86533)) + a helper script for most common management tasks
- Multi-environment deployment with separate Terraform states
- Local tests using [moto](https://github.com/spulec/moto) to mock AWS endpoints
- Keeping development dependencies out of deployed Lambda zips with pipenv

![Architecture](doc/cloudcraft.png)

The infra consists of the following Terraform modules:
- `shared` sets up a Postgres micro-instance and a security group allowing external access. As the name suggests, we're sharing one database with all stages in order to not exceed AWS free tier's 1 micro instance limit; instead stage separation happens at schema level.
- `messaging` sets up an SNS topic for events and an IAM user with publishing permissions. Event producers should use this IAM user's API keys.
- `analytics_db` sets up stage-specific schemas and roles in the shared database.
- `analytics_queue` sets up an SQS queue consuming the events SNS topic. A scheduled Cloudwatch event triggers a consumer Lambda function every 5 minutes. The consumer pulls events out of the SQS queue and fans them out to a worker Lambda which in turn feeds events into the shared database.

## Dependencies

- AWS Command Line Interface
- [invoke](https://github.com/pyinvoke/invoke)
- pip-env >= 8.3.0
- terraform
- [awslogs](https://github.com/jorgebastida/awslogs) (optional)
- An S3 bucket for [storing Terraform remote state](https://www.terraform.io/docs/state/remote.html)

## Set up infrastructure

First set up the shared environment:

1. Navigate to the shared environment directory `infrastructure/shared`.
2. Create a `terraform.tfvars` [secret variables file](https://www.terraform.io/intro/getting-started/variables.html#from-a-file). Check [`infrastructure/shared/terraform.tfvars.sample`](infrastructure/shared/terraform.tfvars.sample) for an example. These files should naturally be kept outside version control.
3. Run `terraform init` to set up a Terraform working directory. You'll be prompted for the name of your remote state bucket. Alternatively you can define the bucket with a `-backend-config='bucket=[BUCKET NAME]'` argument.
4. Run `terraform apply` to build the infra.

Now with the shared infra set up, you can provision individual stages. For example to set up `dev`:

1. First build the Lambda functions: `inv build`.
2. Navigate to the environment directory: e.g. `cd infrastructure/dev`.
3. Repeat the above steps 2-4 to set up the stage-specific resources.
4. Initialize the database: `inv init-db --env dev`.

And we're set! Replace `dev` with `staging`, `prod`, etc to set up additional stages.

## Tasks

Various management tasks are defined in [`tasks.py`](tasks.py). The default environment (`--env`) and AWS profile can be configured in [`invoke.yaml`](invoke.yaml).

Run `inv --list` to see a summary of all available tasks. The most important tasks are as follows:

### Build

`inv build --func [FUNCTION]`: Build a function. Builds all if `--func` is not specified.

### Test

`inv test --func [FUNCTION]`: Run a function's tests. Tests all functions if `--func` is not specified.

### Invoke

`inv invoke [FUNCTION] --env [ENV] --payload [PAYLOAD]`: Invoke a deployed function.

Example:
```bash
inv invoke analytics_worker --env staging --payload '[{"event_id": 12}]'
```

### Update

`inv update [FUNCTION] --env [ENV]`: Quickly update function code without rebuilding dependencies.

## Limitations

Due to [a bug in the Terraform Postgres provider](https://github.com/terraform-providers/terraform-provider-postgresql/issues/16), changing db password variables doesn't actually result in a password update. As a workaround you can manually `DROP ROLE ...` via `psql` and re-apply terraform.

## TODO

- Local invocation
- Set up alembic or similar to manage DB migrations
- An .ignore file to configure files kept out of Lambda zips
