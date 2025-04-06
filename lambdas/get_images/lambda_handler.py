import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)


def handler(event, context):
    date_param = event.get('queryStringParameters', {}).get('date')
    name_param = event.get('queryStringParameters', {}).get('name')

    response = {
        'statusCode': 200,
        'body': {}
    }

    try:
        if date_param is None and name_param is None:
            scan_response = table.scan()
            response['body'] = {
                'items': scan_response.get('Items', [])
            }
        else:
            query_params = {}
            filter_expression = []

            if name_param:
                filter_expression.append(Attr('name').eq(name_param))

            if date_param:
                query_params['KeyConditionExpression'] = Key('createdDateTime').lte(date_param)
                if filter_expression:
                    query_params['FilterExpression'] = filter_expression[0]  # Include name filter if present
            else:
                query_params['IndexName'] = 'NameIndex'
                query_params['KeyConditionExpression'] = Key('name').eq(name_param)

            query_response = table.query(**query_params)
            response['body'] = {
                'items': query_response.get('Items', [])
            }

    except Exception as e:
        response['statusCode'] = 500
        response['body'] = {
            'error': str(e)
        }

    return response
