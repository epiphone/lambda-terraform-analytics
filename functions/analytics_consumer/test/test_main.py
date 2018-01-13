import json
import os
from uuid import uuid4

import boto3
from moto import mock_lambda, mock_sqs
import pytest

os.environ['SQS_URL'] = ''
os.environ['WORKER_LAMBDA_ARN'] = 'test-worker-lambda-arn'


@pytest.fixture
def sqs():
    """
    Return a mocked SQS Queue object.
    """
    mock_sqs().start()
    queue_url = boto3.client('sqs').create_queue(QueueName='test')['QueueUrl']
    queue = boto3.resource('sqs').Queue(queue_url)

    yield queue
    mock_sqs().stop()


@pytest.fixture
def lambda_wrapper(mocker, lambda_context, sqs):
    """
    Set up a mock SQS queue and return the main lambda handler.
    """
    os.environ['SQS_URL'] = sqs.url
    mock_invoke = mocker.patch('main.invoke')
    import main
    return lambda: main.main({}, lambda_context), sqs, mock_invoke


def test_use_aws_test_credentials(lambda_wrapper):
    import main
    creds = main.boto3.DEFAULT_SESSION.get_credentials()
    assert creds.access_key == 'xxx'
    assert creds.secret_key == 'xxx'


def test_no_msgs_in_queue(lambda_wrapper):
    invoke_lambda, queue, mock_invoke = lambda_wrapper

    assert invoke_lambda() == {'processed': 0}
    mock_invoke.assert_not_called()

    msgs_left = queue.receive_messages()
    assert msgs_left == []


def test_single_receive_batch(lambda_wrapper, event):
    invoke_lambda, queue, mock_invoke = lambda_wrapper

    e1, e2 = event(), event()
    queue.send_message(MessageBody=json.dumps({'Message': json.dumps(e1)}))
    queue.send_message(MessageBody=json.dumps({'Message': json.dumps(e2)}))

    assert invoke_lambda() == {'processed': 2}
    mock_invoke.assert_called_once_with(
        FunctionName=os.environ['WORKER_LAMBDA_ARN'],
        InvocationType='Event',
        Payload=json.dumps([e1, e2]))

    msgs_left = queue.receive_messages()
    assert msgs_left == []


@mock_lambda
def test_multiple_receive_batches(lambda_wrapper, mocker, event):
    invoke_lambda, queue, mock_invoke = lambda_wrapper

    n = 87
    batch_size = 10
    batches_n = n // batch_size + 1
    batches = [[event()
                for _ in range(i * 10, min(n, (i + 1) * 10))]
               for i in range(batches_n)]

    for batch in batches:
        queue.send_messages(Entries=[{
            'Id': e['event_id'],
            'MessageBody': json.dumps({
                'Message': json.dumps(e)
            })
        } for e in batch])

    assert invoke_lambda() == {'processed': n}
    calls = [
        mocker.call(
            FunctionName=os.environ['WORKER_LAMBDA_ARN'],
            InvocationType='Event',
            Payload=json.dumps(batch)) for batch in batches
    ]
    mock_invoke.assert_has_calls(calls)

    msgs_left = queue.receive_messages()
    assert msgs_left == []


def test_deduplicate(lambda_wrapper, mocker, event):
    invoke_lambda, queue, mock_invoke = lambda_wrapper
    events = [event() for _ in range(7)]

    # Mock a SQS queue with 2 duplicates among event messages:
    class MockSQSMessage:
        def __init__(self, event):
            self.body = json.dumps({'Message': json.dumps(event)})
            self.message_id = event['event_id']
            self.receipt_handle = str(uuid4())

    msgs = [MockSQSMessage(e) for e in events]
    msgs.insert(2, MockSQSMessage(events[1]))
    msgs.insert(6, MockSQSMessage(events[3]))

    mocker.patch('main.sqs').receive_messages.side_effect = [msgs, []]

    assert invoke_lambda() == {'processed': len(events)}
    mock_invoke.assert_called_once_with(
        FunctionName=os.environ['WORKER_LAMBDA_ARN'],
        InvocationType='Event',
        Payload=json.dumps(events))
