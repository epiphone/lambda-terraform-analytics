from datetime import datetime, timedelta
import json
import logging
import os
from uuid import uuid4

import boto3
from moto import mock_sqs
import pytest

os.environ['SQS_URL'] = 'test-queue-url'
os.environ['WORKER_LAMBDA_ARN'] = 'test-worker-lambda-arn'


@pytest.fixture
def lambda_context():
    class Context(object):
        def __init__(self, timeout=3):
            self.target = datetime.now() + timedelta(seconds=timeout)

        def get_remaining_time_in_millis(self):
            return max((self.target - datetime.now()).seconds, 0) * 1000

    return Context(300)


@pytest.fixture
def event():
    return lambda: {'event_id': str(uuid4()), 'meta': {'x': 10}}


@mock_sqs
def test_main(mocker, event, lambda_context):
    sqs_client = boto3.client('sqs')
    queue_url = sqs_client.create_queue(QueueName='test-queue-url')['QueueUrl']
    e1, e2 = event(), event()
    sqs = boto3.resource('sqs').Queue(queue_url)
    sqs.send_message(MessageBody=json.dumps({'Message': json.dumps(e1)}))
    sqs.send_message(MessageBody=json.dumps({'Message': json.dumps(e2)}))
    os.environ['SQS_URL'] = queue_url

    import main
    mock_invoke = mocker.patch('main.invoke')
    res = main.main({}, lambda_context)
    mock_invoke.assert_called_once_with(
        FunctionName=os.environ['WORKER_LAMBDA_ARN'],
        InvocationType='Event',
        Payload=json.dumps([e1, e2]))

    assert res == {'processed': 2}
