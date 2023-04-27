import json
import os
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

tracer = Tracer()
logger = Logger()

# @metrics.log_metrics


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=False)
def lambda_handler(event, context):

    logger.info(MOMENTO_TOKEN)

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e
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

        print("Setting Key: foo to Value: FOO")
        set_response = cache_client.set(MOMENTO_CACHE_NAME, "foo", "FOO")
        match set_response:
            case CacheSet.Error() as error:
                raise error.inner_exception

        print("Getting Key: foo")
        get_response = cache_client.get(MOMENTO_CACHE_NAME, "foo")
        match get_response:
            case CacheGet.Hit() as hit:
                print(f"Look up resulted in a hit: {hit}")
                print(f"Looked up Value: {hit.value_string!r}")
            case CacheGet.Miss():
                print("Look up resulted in a: miss. This is unexpected.")
            case CacheGet.Error() as error:
                raise error.inner_exception

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
