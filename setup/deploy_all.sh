#!/bin/bash

# Package and deploy API Lambda
cd lambda/api_to_xml
zip function.zip lambda_function.py
aws lambda update-function-code --function-name OAIHarvesterLambda --zip-file fileb://function.zip

# Package and deploy XML-to-JSON Lambda
cd ../xml_to_json
zip function.zip lambda_function.py
aws lambda update-function-code --function-name XMLtoJSONLambda --zip-file fileb://function.zip

echo "✅ All Lambda functions deployed."

# TODO: Add IAM role creation and S3 trigger setup here
