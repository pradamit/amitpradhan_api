import json
import base64
import boto3
import os
import uuid

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']  # Set this in your SAM template


class InvalidImageFormat(Exception):
    pass


def handler(event, context):

    if event['isBase64Encoded']:
        body = base64.b64decode(event['body'])
    else:
        raise InvalidImageFormat('The image is not in base64 format')

    file_name = str(uuid.uuid4())

    s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=body)

    response = {
        'statusCode': 200,
        'body': json.dumps({'message': f'Image uploaded successfully with filename : {file_name}'})
    }

    return response
