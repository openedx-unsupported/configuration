#!/usr/bin/python

import sys

import boto3

aws_access_key_id, aws_secret_access_key, rest_api_id = sys.argv[1:]
client = boto3.client('apigateway', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# TODO Pull https://github.com/edx/api-manager/blob/master/swagger/api.yaml, and compile with swagger-codegen
# swagger-codegen generate -l swagger -i swagger/api.yaml
with open('swagger.json') as body:
    client.put_rest_api(restApiId=rest_api_id, body=body)
