import boto3

events = boto3.client('events')
lambda_client = boto3.client('lambda')

# Step 1: Create CloudWatch Event Rule (e.g., run every day at 2 AM UTC)
response = events.put_rule(
    Name='arxiv-weekly-trigger',
    ScheduleExpression='cron(0 2 ? * MON *)',  # Every Monday at 2 AM UTC
    State='ENABLED',
    Description='Weekly trigger for arXiv data pipeline'
)

rule_arn = response['RuleArn']

# Step 2: Add Lambda function as a target
lambda_function_name = 'arxiv-lambda-1'
lambda_arn = lambda_client.get_function(FunctionName=lambda_function_name)['Configuration']['FunctionArn']

events.put_targets(
    Rule='arxiv-weekly-trigger',
    Targets=[
        {
            'Id': 'arxiv-lambda-1-target',
            'Arn': lambda_arn
        }
    ]
)

# Step 3: Grant CloudWatch Events permission to invoke the Lambda
lambda_client.add_permission(
    FunctionName=lambda_function_name,
    StatementId='AllowExecutionFromCloudWatchEvents',
    Action='lambda:InvokeFunction',
    Principal='events.amazonaws.com',
    SourceArn=rule_arn
)
