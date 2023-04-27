import json
import os
import boto3
from momento import CacheClient, Configurations, CredentialProvider
from momento.responses import CacheGet, CacheSet, CreateCache
from datetime import timedelta


# import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

DYNAMO_TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']
MOMENTO_TOKEN = os.environ['MOMENTO_TOKEN']
MOMENTO_CACHE_NAME = os.environ['MOMENTO_CACHE_NAME']

# dynamodb = boto3.resource('dynamodb')
# dynamo_table = dynamodb.Table(DYNAMO_TABLE_NAME)
# primarykey='single_default'

tracer = Tracer()
logger = Logger()

# @metrics.log_metrics


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=False)
def lambda_handler(event, context):

    primarykey = event['pathParameters']['primarykey']
    print(f"Path Parameter is {primarykey}")

    # logger.info(MOMENTO_TOKEN)

    with CacheClient(
        configuration=Configurations.Laptop.v1(),
        credential_provider=CredentialProvider.from_environment_variable("MOMENTO_TOKEN"),
        default_ttl=timedelta(seconds=300),
    ) as cache_client:
        create_cache_response = cache_client.create_cache(MOMENTO_CACHE_NAME)
        match create_cache_response:
            case CreateCache.CacheAlreadyExists():
                print(f"Cache with name: {MOMENTO_CACHE_NAME} already exists.")
            case CreateCache.Error() as error:
                raise error.inner_exception



        print(f"Getting Key: {primarykey}")
        get_response = cache_client.get(MOMENTO_CACHE_NAME, primarykey)
        match get_response:
            case CacheGet.Hit() as hit:
                print(f"Look up resulted in a hit: {hit}")
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "data from Momento",
                        "data": hit.value_string
                    }),
                }  
            case CacheGet.Miss():
                # print("Look up resulted in a: miss. This is unexpected.")
                print(f"Setting Key: {primarykey}")
                dynamodb = boto3.resource('dynamodb')
                dynamo_table = dynamodb.Table(DYNAMO_TABLE_NAME)
                dynamo_table_response = dynamo_table.get_item(
                    Key={
                        'primarykey': str(primarykey)
                    }
                )
                data = dynamo_table_response.get('Item', {})
                # print(dynamo_table_response)
                # print(data)
                set_response = cache_client.set(MOMENTO_CACHE_NAME, primarykey, json.dumps(data))
                match set_response:
                    case CacheSet.Error() as error:
                        raise error.inner_exception
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "data from Dynamo",
                        "data": json.dumps(data)
                    }),
                }                
            case CacheGet.Error() as error:
                raise error.inner_exception

    return None
