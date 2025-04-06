import os
import json
import pytest
import boto3
from moto import mock_dynamodb
from lambdas.get_images.lambda_handler import handler

TABLE_NAME = "MyTable"


@mock_dynamodb
def setup_dynamodb():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'createdDateTime', 'KeyType': 'HASH'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'createdDateTime', 'AttributeType': 'S'},
            {'AttributeName': 'name', 'AttributeType': 'S'},
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    table.put_item(Item={'createdDateTime': '2023-01-01T00:00:00Z', 'name': 'test_image_1'})
    table.put_item(Item={'createdDateTime': '2023-01-02T00:00:00Z', 'name': 'test_image_2'})

    os.environ['TABLE_NAME'] = TABLE_NAME


@pytest.fixture
def dynamodb_setup():
    setup_dynamodb()
    yield


def test_handler_scan(dynamodb_setup):
    event = {
        'queryStringParameters': {}
    }

    response = handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['items']) == 2


def test_handler_query_by_name(dynamodb_setup):
    event = {
        'queryStringParameters': {
            'name': 'test_image_1'
        }
    }

    response = handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['items']) == 1
    assert body['items'][0]['name'] == 'test_image_1'


def test_handler_query_by_date(dynamodb_setup):
    event = {
        'queryStringParameters': {
            'date': '2023-01-02T00:00:00Z'
        }
    }

    response = handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['items']) == 0


def test_handler_query_by_name_and_date(dynamodb_setup):
    event = {
        'queryStringParameters': {
            'name': 'test_image_2',
            'date': '2023-01-02T00:00:00Z'
        }
    }

    response = handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body['items']) == 1
    assert body['items'][0]['name'] == 'test_image_2'
