import json
import base64
import boto3
import os
import uuid
import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET_NAME = os.environ['BUCKET_NAME']
TABLE_NAME = os.environ['TABLE_NAME']

table = dynamodb.Table(TABLE_NAME)


class InvalidImageFormat(Exception):
    pass


class InvalidRequest(Exception):
    pass


def handler(event, context):
    try:
        image = event['body']['image']
        image_name = event['body']['name']
        image_metadata = event['body']['metadata']
        time_now = datetime.datetime.now(datetime.timezone.utc)
        body = base64.b64decode(image)
    except KeyError as exp:
        raise InvalidRequest(f'Invalid request. Required field not found {exp}')
    except Exception as exp:
        raise InvalidImageFormat(f'Upload failed due to {exp.args[0]}')

    file_name = str(uuid.uuid4())

    s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=body)

    try:
        table.put_item(
            Item={
                'id': file_name,
                'name': image_name,
                'createdDateTime': time_now.isoformat(),
                'metadata': image_metadata
            }
        )
    except Exception as exp:
        raise InvalidImageFormat(f'DynamoDB upload failed due to {exp.args[0]}')

    response = {
        'statusCode': 200,
        'body': json.dumps({'message': f'Image uploaded successfully with filename : {file_name}'})
    }

    return response
