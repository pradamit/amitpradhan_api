import os
import json
import base64
import boto3
import pytest
from moto import mock_s3, mock_dynamodb

from lambdas.upload.lambda_handler import handler  # Adjust import according to your module name


@pytest.fixture(scope='module')
def aws_setup():
    bucket_name = 'test-bucket'
    table_name = 'test-table'

    # Mock S3
    with mock_s3():
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket=bucket_name)

        # Mock DynamoDB
        with mock_dynamodb():
            dynamodb = boto3.resource('dynamodb')
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'N'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )

            # Set environment variables
            os.environ['BUCKET_NAME'] = bucket_name
            os.environ['TABLE_NAME'] = table_name

            yield  # This allows the test to run


def test_handler_success(aws_setup):
    image_data = base64.b64encode(b'test_image_data').decode('utf-8')
    event = {
        'body': {
            'image': image_data,
            'name': 'test_image.png',
            'metadata': {'key': 'value'}
        }
    }

    response = handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'Image uploaded successfully with filename' in body['message']

    # Check S3
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=os.environ['BUCKET_NAME'])
    assert 'Contents' in response
    assert len(response['Contents']) > 0

    # Check DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    image_id = int(body['message'].split(': ')[-1])
    response = table.get_item(Key={'id': image_id})
    assert 'Item' in response
    assert response['Item']['name'] == 'test_image.png'
