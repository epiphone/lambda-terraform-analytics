import os
import re

import pytest

os.environ['DB_URL'] = 'test_db_url'
os.environ['TABLE_NAME'] = 'test_schema.test_table'


@pytest.fixture
def handler(mocker, lambda_context):
    mocker.patch('psycopg2.extras.LoggingConnection')
    import main
    return lambda event: main.main(event, lambda_context)


def test_dont_store_when_no_events(mocker, handler):
    mock_execute_values = mocker.patch('main.execute_values')
    assert handler([]) == {'processed': 0}
    mock_execute_values.assert_not_called()


def test_skip_events_with_missing_keys(mocker, event, handler):
    events = [{}, event(), {'event_id': 'invalid_event'}]
    mock_execute_values = mocker.patch('main.execute_values')
    assert handler(events) == {'processed': 1}
    mock_execute_values.assert_called_once
    values = mock_execute_values.call_args[0][2]
    assert len(values) == 1


def test_store_events(mocker, event, handler):
    events = [event() for _ in range(3)]
    mock_execute_values = mocker.patch('main.execute_values')
    assert handler(events) == {'processed': len(events)}
    assert mock_execute_values.call_count == 1

    _, query, values = mock_execute_values.call_args[0]
    keys = [k.strip() for k in re.findall(r'\((.+)\)', query)[0].split(', ')]

    for event_index in range(len(events)):
        for key_index, key in enumerate(keys):
            assert values[event_index][key_index] == events[event_index][key]
