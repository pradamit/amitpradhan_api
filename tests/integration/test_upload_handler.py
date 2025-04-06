import json
import base64
import unittest
from unittest.mock import patch
import boto3
from moto import mock_s3, mock_dynamodb

# Import the handler function
from lambdas.upload.lambda_handler import handler  # Adjust import according to your module name


class TestLambdaHandler(unittest.TestCase):
    @mock_s3
    @mock_dynamodb
    def setUp(self):
        self.bucket_name = 'test-bucket'
        self.table_name = 'test-table'

        s3 = boto3.client('s3')
        s3.create_bucket(Bucket=self.bucket_name)

        dynamodb = boto3.resource('dynamodb')
        dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'N'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )

        self.patch_env = patch.dict('os.environ', {
            'BUCKET_NAME': self.bucket_name,
            'TABLE_NAME': self.table_name
        })
        self.patch_env.start()

    def tearDown(self):
        self.patch_env.stop()

    def test_handler_success(self):
        image_data = base64.b64encode(b'test_image_data').decode('utf-8')
        event = {
            'body': {
                'image': image_data,
                'name': 'test_image.png',
                'metadata': {'key': 'value'}
            }
        }

        response = handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('Image uploaded successfully with filename', body['message'])

        s3 = boto3.client('s3')
        response = s3.list_objects_v2(Bucket=self.bucket_name)
        self.assertTrue('Contents' in response)
        self.assertGreater(len(response['Contents']), 0)

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(self.table_name)
        response = table.get_item(Key={'id': int(body['message'].split(': ')[-1])})
        self.assertIn('Item', response)
        self.assertEqual(response['Item']['name'], 'test_image.png')
