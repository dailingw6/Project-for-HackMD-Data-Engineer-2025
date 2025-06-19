#  Setup Guide

This guide walks through the complete setup process for deploying and running the arXiv metadata pipeline.

---

##  Requirements

- AWS CLI configured with sufficient permissions
- Python 3.9+
- Permissions to deploy Lambda functions, S3 event triggers, IAM roles, and Glue jobs

---

##  Step-by-Step Setup

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/arxiv-pipeline.git
cd arxiv-pipeline
```

### 2. Create S3 Bucket

```bash
aws s3 mb s3://arxiv-raw-data-bucket
```

### 3. Deploy IAM Roles (via Console or CLI)

Use the IAM policies from:

```bash
setup/iam/
```

Attach them to:

- `OAIHarvesterLambda`
- `XMLtoJSONLambda`
- `GlueETLJob`

### 4. Deploy Lambda Functions

```bash
bash setup/deploy_all.sh
```

This script will:

- Package the Lambda code
- Upload it to AWS
- (Optional) Attach permissions

### 5. Set Up Event Triggers

Use scripts or console to configure:

-  `APItoXML`: EventBridge (every 5 min)
-  `XMLtoJSON`: S3 trigger on `raw/latest/{date}/`

You can also use the script:

```bash
bash setup/glue_trigger_setup.sh
```

### 6. Test End-to-End

- Manually trigger API Lambda if needed:

```bash
aws lambda invoke --function-name OAIHarvesterLambda out.json
```

- Check S3 for: `raw/latest/{run_date}/part_0.xml`
- Confirm `parsed/{run_date}/` fills with `.jsonl` files

### 7. Trigger Glue Job

```bash
aws glue start-job-run --job-name GLUEETLJob
```

Output tables will be written to:

```
s3://arxiv-raw-data-bucket/tables/
```

---

##  Install Python Dependencies (Locally)

If you want to simulate Lambda logic locally:

```bash
pip install boto3 requests
```

---

##  Tips & Warnings

- Ensure Lambda timeout is high enough (≥ 1 min for OAI)
- Validate manifest file status before triggering Glue
- Monitor CloudWatch logs for each Lambda



