#!/bin/bash

# This script sets up an AWS Glue trigger to run the ETL job when desired.
# You must have already created the Glue job manually or via IaC.

GLUE_JOB_NAME="GLUEETLJob"
TRIGGER_NAME="TriggerGLUEETLOnDemand"

# Create a trigger that is on-demand (you can modify to be scheduled)
aws glue create-trigger \
    --name $TRIGGER_NAME \
    --type ON_DEMAND \
    --actions '[{"JobName": ""$GLUE_JOB_NAME""}]' \
    --start-on-creation

# Optional: Trigger the job manually
# aws glue start-trigger --name $TRIGGER_NAME

# Check that the trigger was created
aws glue get-trigger --name $TRIGGER_NAME
