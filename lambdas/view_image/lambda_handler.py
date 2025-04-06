import json
import boto3
import base64
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']


def handler(event, context):
    image_id = event.get('pathParameters', {}).get('id')

    if image_id:
        return get_image_by_id(image_id)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'ID parameter is required'})
        }


def get_image_by_id(image_id):
    try:
        # Fetch the image from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=image_id)
        image_data = response['Body'].read()

        # Encode the image data in base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/jpeg',  # Adjust the content type based on your image format
                'Content-Disposition': f'attachment; filename="{image_id}"'
            },
            'body': image_base64,
            'isBase64Encoded': True  # Indicate that the body is base64-encoded
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
