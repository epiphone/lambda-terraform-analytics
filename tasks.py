"""
Management tasks for the analytics service.
"""
import base64
from datetime import datetime
import json
import re
import os
import uuid

from invoke import task

ROOT = os.path.dirname(os.path.realpath(__file__))
FUNCTIONS_PATH = os.path.join(ROOT, 'functions')
PRECOMPILED_PATH = os.path.join(ROOT, 'precompiled')


@task(iterable=['func'])
def build(ctx, func=None):
    """
    Build Lambda handlers. Specify --func to only build specific functions.
    """
    for f in (func if func else _list_functions()):
        with ctx.cd(os.path.join(FUNCTIONS_PATH, f)):
            print('Building', f)
            # Install pip production dependencies:
            ctx.run('mkdir build', hide=True, warn=True)
            ctx.run('rm -r ./build/*', hide=True, warn=True)
            ctx.run(
                'pip install -r <(pipenv lock -r) -t build',
                echo=True,
                warn=True)

            # Overwrite dynamically linked libraries with precompiled ones:
            precompiled = next(os.walk(PRECOMPILED_PATH))[1]
            for dep in ctx.run('ls build', hide=True).stdout.split():
                if dep in precompiled:
                    source = os.path.join(PRECOMPILED_PATH, dep)
                    target = os.path.join('build', dep)
                    ctx.run(f'rm -rf {target}')
                    ctx.run(f'cp -r {source} {target}')
                    _printc(f'Overwrote build/{dep} with {source}!')

            # Copy source:
            ctx.run('cp -r *.py build/')


@task
def gen_event(ctx):
    """
    Print out a randomly generated sample event in JSON.
    """
    event = json.dumps({
        'event_id': str(uuid.uuid4()),
        'event_timestamp': datetime.utcnow().isoformat() + 'Z',
        'event_type': '_test_event',
        'event_version': '1.0',
        'app_title': '_test_app',
        'app_version': '1.0',
        'user_id': str(uuid.uuid4()),
        'user_name': 'test@user.com',
        'meta': {},
        'user_payload': {}
    })
    print(event)
    return event


@task
def init_db(ctx, env=None):
    """
    Initialize the analytics database. Operation is idempotent so running it
    repeatedly shouldn't cause any adverse effects.
    """
    env = env or ctx['env']
    with ctx.cd(os.path.join(ROOT, 'infrastructure', 'shared')):
        db_url = ctx.run('terraform output analytics_db_url', hide=True).stdout

        with ctx.cd(os.path.join(ROOT, 'infrastructure', env)):
            output = json.loads(
                ctx.run('terraform output -json', hide=True).stdout)
            sql_script = INIT_ANALYTICS_DB_SCRIPT.format(
                table=output['analytics_db_schema']['value'] + '.events',
                consumer=output['analytics_db_consumer_username']['value'],
                producer=output['analytics_db_producer_username']['value'])
            ctx.run(f"echo '{sql_script}' | psql {db_url}", echo=True)


@task
def invoke(ctx, func, env=None, payload=None):
    """
    Invoke a function.
    """
    output_file_name = '.tmp_output'
    with ctx.cd(ROOT):
        ret = ctx.run(
            f"""aws --profile {ctx['profile']} lambda invoke \
            --function-name {func}_{env or ctx['env']} \
            --invocation-type RequestResponse \
            --log-type Tail \
            --payload '{payload or '{}'}' \
            {output_file_name}""",
            hide=True,
            warn=True)
        print(ret.command.replace('  ', ''))

        if ret.ok:
            log_result = re.findall(r'LogResult": "(.+)"', ret.stdout)[0]
            print(base64.b64decode(log_result).decode('utf-8'))
            ctx.run(f'cat {output_file_name}')
            ctx.run(f'rm {output_file_name}')
        else:
            print(ret.stderr)


@task
def log(ctx, func, env=None):
    """
    Stream function logs via awslogs.
    """
    prof, env = ctx['profile'], env or ctx['env']
    ctx.run(f'awslogs get --profile {prof} /aws/lambda/{func}_{env} --watch')


@task
def psql(ctx):
    """
    Connect to the shared analytics db using admin credentials stored in .tfvars.
    """
    with ctx.cd(os.path.join(ROOT, 'infrastructure', 'shared')):
        db_url = ctx.run('terraform output analytics_db_url', hide=True).stdout
        ctx.run(f'psql {db_url}', pty=True)


@task
def package(ctx, func, package_name='package.zip'):
    """
    Package a built function into a zip file.
    """
    build_path = os.path.join(FUNCTIONS_PATH, func, 'build')
    with ctx.cd(build_path):
        zip_path = os.path.join(FUNCTIONS_PATH, func, package_name)
        ctx.run(f'zip -x "*.pyc" -x \*.dist-info\* -r {zip_path} .', echo=True)


@task
def publish_event(ctx, env=None, n=1):
    """
    Publish randomized test events on the events SNS topic.
    """
    with ctx.cd(os.path.join(ROOT, 'infrastructure', env or ctx['env'])):
        topic = ctx.run(
            'terraform output messaging_topic_arn', hide=True).stdout
        for _ in range(n):
            event = gen_event(ctx)
            ctx.run(
                f"aws sns publish --message '{event}' --topic-arn {topic}",
                echo=True)


@task(iterable=['func'])
def test(ctx, func=None):
    """
    Test Lambda handlers. Specify --func to only test specific functions.
    """
    for f in (func if func else _list_functions()):
        with ctx.cd(os.path.join(FUNCTIONS_PATH, f)):
            print('Testing', f)
            ctx.run('pipenv install --dev')
            ctx.run('pipenv run python -m pytest -s')


@task
def update(ctx, func, env=None):
    """
    Quickly update function code without rebuilding dependencies.
    """
    # TODO support multiple funcs
    profile, env = ctx['profile'], env or ctx['env']
    func_path = os.path.join(FUNCTIONS_PATH, func)

    with ctx.cd(func_path):
        build_dir = os.path.join(func_path, 'build')
        if not (os.path.isdir(build_dir) and os.listdir(build_dir)):
            build(ctx, [func])
        else:
            ctx.run('cp -r ./*.py build/')  # TODO: handle nested dirs

        zip_file = 'package.zip'
        package(ctx, func, package_name=zip_file)
        ctx.run(
            f'aws --profile {profile} lambda update-function-code --function-name {func}_{env} --zip-file fileb://{zip_file}',
            echo=True)


def _list_functions():
    return next(os.walk(FUNCTIONS_PATH))[1]


def _printc(text, col='\033[0;33m'):
    """Print a line in color, defaulting to yellow."""
    print(f'{col}{text}\033[0m')


INIT_ANALYTICS_DB_SCRIPT = """
CREATE TABLE IF NOT EXISTS {table} (
  id                    bigserial PRIMARY KEY,
  event_id              varchar(36) NOT NULL,
  event_timestamp       timestamp NOT NULL,
  event_type            varchar(128) NOT NULL,
  event_version         varchar(12) NOT NULL,
  app_title             varchar(128) NOT NULL,
  app_version           varchar(12) NOT NULL,
  user_id               varchar(128) NOT NULL,
  user_name             varchar(128) NOT NULL,
  created_at            timestamp DEFAULT current_timestamp,
  meta                  jsonb,
  token_payload         jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS event_id on {table}(event_id);
CREATE INDEX IF NOT EXISTS event_type on {table}(event_type);

GRANT SELECT, INSERT, UPDATE ON {table} TO "{producer}";
GRANT SELECT ON {table} TO "{consumer}";
GRANT USAGE, SELECT, UPDATE ON {table}_id_seq TO "{producer}";
GRANT USAGE, SELECT ON {table}_id_seq TO "{consumer}";
"""
