"""
Analytics consumer - pull events from analytics events queue and fan out to
worker lambdas.
"""
import logging
import json
import os

from psycopg2.extras import execute_values, LoggingConnection

DB_URL = os.environ['DB_URL']
TABLE_NAME = os.environ['TABLE_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # set to DEBUG to log SQL queries
conn = LoggingConnection(DB_URL)
conn.initialize(logger)

EVENT_KEYS = [
    'event_id', 'event_timestamp', 'event_type', 'event_version', 'app_title',
    'app_version', 'user_id', 'user_name', 'meta', 'token_payload'
]
JSON_FIELDS = ['meta', 'token_payload']
INSERT_QUERY = f"""
    INSERT INTO {TABLE_NAME} ({', '.join(EVENT_KEYS)}) VALUES %s
    ON CONFLICT (event_id) DO NOTHING
"""


def main(event, context):
    logger.info('Received %d event items', len(event))
    values = []
    for e in event:
        for json_key in JSON_FIELDS:
            e[json_key] = json.dumps(e.get(json_key, {}))
        try:
            values.append(tuple(e[key] for key in EVENT_KEYS))
        except KeyError:
            logger.warn('Invalid event object, skipping: %s', e)

    if values:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, INSERT_QUERY, values)

    logger.info('Processed %d event(s), skipped %d', len(values),
                len(event) - len(values))
    return {'processed': len(values)}
