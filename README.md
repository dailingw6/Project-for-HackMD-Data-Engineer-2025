# arxiv-pipeline

A scalable and fault-tolerant data pipeline for harvesting, processing, and transforming arXiv metadata using AWS services. Built for the HackMD Data Engineer Case Study.

## Overview

This project ingests metadata from arXiv using the OAI-PMH protocol, processes XML into structured JSON, and transforms it into relational-style tables using AWS Glue.

### Key Features

* Scheduled incremental harvesting of arXiv metadata
* XML parsing and JSON normalization via Lambda
* Glue ETL job that produces dimensional tables in Parquet
* S3-based data lake with backup and staging
* Supports analytical dashboards, institutional rankings, NLP-based recommendations

## Tech Stack

| Layer          | Tools                                              |
| -------------- | -------------------------------------------------- |
| Ingestion      | AWS Lambda (Python), CloudWatch, S3                |
| Processing     | Python, XML parsing, JSON Lines                    |
| Storage        | S3 (staging/latest/backup), Athena-ready structure |
| Transformation | AWS Glue (PySpark)                                 |
| Monitoring     | CloudWatch Logs, manifest status                   |

## Directory Structure

```
arxiv-pipeline/
├── README.md                     # Project overview and quickstart
├── setup/                        # Infra setup scripts
├── lambda/                       # Lambda function code
├── glue/                         # Glue ETL job code and schema
├── docs/                         # Markdown documentation
└── tests/                        # Unit test scripts
```

## Modules

### 1. `lambda/api_to_xml`

* Scheduled via EventBridge to run every 5–15 minutes
* Fetches new arXiv records using OAI-PMH
* Stores XML parts in `s3://arxiv-raw-data-bucket/raw/latest/{run_date}/`

### 2. `lambda/xml_to_json`

* Triggered by S3 upload events
* Converts XML into newline-delimited JSON (NDJSON)
* Saves to `parsed/{run_date}/`

### 3. `glue/glue_etl_job.py`

* Reads parsed JSON
* Produces:

  * `paper`, `contributor`, `paper_contributor`
  * `category`, `paper_category`, `paper_submission`
* Outputs in Parquet under `tables/`

## Quickstart

```bash
# Install requirements
pip install boto3

# Deploy lambdas
bash setup/deploy_all.sh

# Manually run Glue job
aws glue start-job-run --job-name GLUEETLJob
```

## Test

```bash
pytest tests/
```

## Future Enhancements

* Glue catalog integration
* Real-time alerts for manifest failures
* Author disambiguation logic
* Semantic vector embedding pipeline for recommendations


