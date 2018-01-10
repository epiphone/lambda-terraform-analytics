"""
Management tasks for the analytics service.
"""
import base64
from datetime import datetime
import json
import os
import uuid

from invoke import task

ROOT = os.path.dirname(os.path.realpath(__file__))
FUNCTIONS_PATH = os.path.join(ROOT, 'functions')
PRECOMPILED_PATH = os.path.join(ROOT, 'precompiled')


@task(help={'func': 'The target function to build'}, iterable=['func'])
def build(ctx, func=None):
    """
    Build Lambda handlers. Specify --func to only build one function.
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
def invoke(ctx, env, func, payload=None):
    """
    Invoke a function.
    """
    output_file_name = '.tmp_output'
    with ctx.cd(ROOT):
        ret = ctx.run(
            f"""aws lambda invoke \
            --function-name {func}_{env} \
            --invocation-type RequestResponse \
            --log-type Tail \
            --payload '{payload or '{}'}' \
            {output_file_name}""",
            hide=True,
            warn=True)
        print(ret.command.replace('  ', ''))

        if ret.ok:
            print(base64.b64decode(ret.stdout.split()[-2]).decode('utf-8'))
            ctx.run(f'cat {output_file_name}')
            ctx.run(f'rm {output_file_name}')
        else:
            print(ret.stderr)


@task
def log(ctx, env, func):
    """
    Stream function logs via awslogs.
    """
    ctx.run(f'awslogs get /aws/lambda/{func}_{env} --watch')


@task
def psql(ctx, env):
    """
    Connect to analytics db using admin credentials stored in .tfvars.
    """
    with ctx.cd(os.path.join(ROOT, 'infrastructure', env)):
        ret = ctx.run('terraform output shared_analytics_db_url', hide=True)
        ctx.run(f'psql {ret.stdout}', pty=True)


@task
def publish_event(ctx, env, n=1):
    """
    Publish randomized test events on the events SNS topic.
    """
    with ctx.cd(os.path.join(ROOT, 'infrastructure', env)):
        topic = ctx.run(
            'terraform output messaging_topic_arn', hide=True).stdout
        for _ in range(n):
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
            ctx.run(f"aws sns publish --message '{event}' --topic-arn {topic}")


@task
def update(ctx, env, func):
    """
    Quickly update function code without rebuilding dependencies.
    """
    # TODO support multiple funcs, create zip in function root folder
    target = os.path.join(FUNCTIONS_PATH, func)
    with ctx.cd(target):
        build_dir = os.path.join(target, 'build')
        if not (os.path.isdir(build_dir) and os.listdir(build_dir)):
            build(ctx, func)
        else:
            ctx.run('cp -r ./*.py build/')

        zip_path = os.path.join('~/tmp', f'{func}_{env}.zip')
        with ctx.cd('build'):
            ctx.run(f'zip -x "*.pyc" -x \*.dist-info\* -r {zip_path} .')
            ctx.run(
                f'aws lambda update-function-code --function-name {func}_{env} --zip-file fileb://{zip_path}'
            )


# @task
# def package(ctx):
#     """
#     Package lambda code with dependencies into a .zip file for uploading.
#     """
#     with ctx.cd(os.path.join(ROOT, 'build')):
#         ctx.run(f'zip -x "*.pyc" -r {os.path.join("..", PACKAGE_NAME)} .')


def _list_functions():
    return next(os.walk(FUNCTIONS_PATH))[1]


def _printc(text, col='\033[0;33m'):
    """Print a line in color, defaulting to yellow."""
    print(f'{col}{text}\033[0m')
