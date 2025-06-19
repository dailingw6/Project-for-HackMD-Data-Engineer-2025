import boto3
s3 = boto3.client('s3')

bucket_name = 'your-bucket-name'
lambda_function_arn = 'arn:aws:lambda:region:acct-id:function:your-etl-lambda'

s3.put_bucket_notification_configuration(
    Bucket=bucket_name,
    NotificationConfiguration={
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': lambda_function_arn,
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'prefix', 'Value': 'raw/'},  # only for raw folder
                            {'Name': 'suffix', 'Value': '.json'}  # only JSON files
                        ]
                    }
                }
            }
        ]
    }
)
