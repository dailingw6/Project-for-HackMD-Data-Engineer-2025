import boto3
lambda_client = boto3.client('lambda')

lambda_client.add_permission(
    FunctionName='your-etl-lambda',
    StatementId='AllowS3Invoke',
    Action='lambda:InvokeFunction',
    Principal='s3.amazonaws.com',
    SourceArn=f'arn:aws:s3:::{bucket_name}',
    SourceAccount='your-account-id'
)
