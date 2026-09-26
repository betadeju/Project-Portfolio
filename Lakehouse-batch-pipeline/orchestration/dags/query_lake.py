import boto3, os
client = boto3.client('s3',
    endpoint_url='http://garage:3900',
    aws_access_key_id=os.environ['STORAGE_ACCESS_KEY'],
    aws_secret_access_key=os.environ['STORAGE_SECRET_KEY']
)
response = client.list_objects_v2(Bucket='weather-lake', Prefix='gold/')
if 'Contents' in response:
    for obj in response['Contents']:
        print("{obj['Size']} bytes \t {obj['Key']}")
else:
    print('No files found in gold/')