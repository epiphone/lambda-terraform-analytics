from datetime import datetime, timedelta
import os
from uuid import uuid4

import pytest

os.environ['AWS_ACCESS_KEY_ID'] = 'xxx'
os.environ['AWS_DEFAULT_REGION'] = 'eu-central-1'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'xxx'
os.environ['SESSION'] = 'xxx'


@pytest.fixture
def lambda_context():
    """
    Return a mock Lambda Context instance to be used in manual invocation.
    """

    class Context(object):
        def __init__(self, timeout=3):
            self.target = datetime.now() + timedelta(seconds=timeout)

        def get_remaining_time_in_millis(self):
            return max((self.target - datetime.now()).seconds, 0) * 1000

    return Context(300)


@pytest.fixture
def event():
    """
    Return random analytics event factory function.
    """
    return lambda: {'event_id': str(uuid4()), 'meta': {'x': 10}}
