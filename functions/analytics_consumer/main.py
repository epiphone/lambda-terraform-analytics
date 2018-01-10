"""
Analytics consumer - pull events from analytics events queue and fan out to
worker lambdas.
"""
import logging
import json
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQS_URL = os.environ['SQS_URL']
WORKER_LAMBDA_ARN = os.environ['WORKER_LAMBDA_ARN']

invoke = boto3.client('lambda').invoke
sqs = boto3.resource('sqs').Queue(SQS_URL)


def main(event, context):
    processed = 0
    handled_mgs_ids = set()

    while context.get_remaining_time_in_millis() > 10000:
        message_bodies = []
        messages_to_delete = []
        msgs = sqs.receive_messages(
            MaxNumberOfMessages=10, VisibilityTimeout=0, WaitTimeSeconds=1)

        # Deduplicate and parse message bodies:
        for m in msgs:
            if m.message_id in handled_mgs_ids:
                continue
            handled_mgs_ids.add(m.message_id)
            message_bodies.append(json.loads(json.loads(m.body)['Message']))
            messages_to_delete.append({
                'Id': m.message_id,
                'ReceiptHandle': m.receipt_handle
            })

        if not messages_to_delete:
            break

        invoke(
            FunctionName=WORKER_LAMBDA_ARN,
            InvocationType='Event',
            Payload=json.dumps(message_bodies))
        processed += len(messages_to_delete)
        sqs.delete_messages(Entries=messages_to_delete)

    return {'processed': processed}
