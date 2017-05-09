import boto3

client = boto3.client('ecs')
services = client.list_services()
print services