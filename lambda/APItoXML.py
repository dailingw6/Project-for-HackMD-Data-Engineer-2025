import os
import json
import requests
import boto3
import time
import logging
from urllib.parse import urlencode
from botocore.exceptions import ClientError
from datetime import datetime
from random import uniform

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS client
s3 = boto3.client('s3')

# Environment config
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 1000))
S3_BUCKET = os.environ.get("S3_BUCKET", "arxiv-raw-data-bucket")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))

RUN_DATE = datetime.utcnow().strftime("%Y-%m-%d")
ARXIV_BASE = "http://export.arxiv.org/api/query"

LATEST_PREFIX = f"raw/latest/{RUN_DATE}/"
BACKUP_PREFIX = f"raw/backup/{RUN_DATE}/"
STAGING_PREFIX = f"raw/staging/{RUN_DATE}/"

def fetch_arxiv_chunk(start_index):
    query_params = {
        "search_query": "all",
        "start": start_index,
        "max_results": CHUNK_SIZE,
        "sortBy": "submittedDate",
        "sortOrder": "ascending"
    }
    url = f"{ARXIV_BASE}?{urlencode(query_params)}"

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            logger.info(f"[{start_index}] Requesting: {url}")
            response = requests.get(url, timeout=10)

            if response.status_code == 200 and "<entry>" in response.text:
                return response.text
            raise Exception(f"Unexpected response (status: {response.status_code})")
        except Exception as e:
            wait_time = uniform(2, 2 ** retries)
            logger.warning(f"[{start_index}] Retry {retries+1}/{MAX_RETRIES} - Error: {e}, waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            retries += 1

    raise RuntimeError(f"[{start_index}] Failed to fetch after {MAX_RETRIES} retries")

def upload_chunk_to_s3(content, key):
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=content)
        logger.info(f"Uploaded to s3://{S3_BUCKET}/{key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to upload {key}: {e}")
        return False

def write_manifest(successful, failed):
    manifest = {
        "run_date": RUN_DATE,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "expected_chunks": len(successful) + len(failed),
        "successful_chunks": len(successful),
        "failed_chunks": len(failed),
        "status": "SUCCESS" if len(failed) == 0 else "FAILED",
        "chunks": successful,
        "failed_indexes": failed
    }
    manifest_key = f"{STAGING_PREFIX}manifest.json"
    upload_chunk_to_s3(json.dumps(manifest), manifest_key)
    return manifest

def copy_folder(source_prefix, dest_prefix):
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=source_prefix):
        for obj in page.get('Contents', []):
            src_key = obj['Key']
            dest_key = dest_prefix + src_key[len(source_prefix):]
            copy_source = {'Bucket': S3_BUCKET, 'Key': src_key}
            s3.copy_object(Bucket=S3_BUCKET, CopySource=copy_source, Key=dest_key)
            logger.info(f"Copied {src_key} → {dest_key}")

def latest_manifest_successful():
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=f"raw/latest/{RUN_DATE}/manifest.json")
        manifest = json.loads(response['Body'].read().decode())
        return manifest.get("status") == "SUCCESS"
    except Exception as e:
        logger.warning("No valid manifest found in latest/: " + str(e))
        return False

def lambda_handler(event, context):
    logger.info(f"Starting arXiv data collection run: {RUN_DATE}")
    successful_chunks = []
    failed_chunks = []

    start_index = 0
    while True:
        try:
            content = fetch_arxiv_chunk(start_index)

            if "<entry>" not in content:
                logger.info(f"No entries found at index {start_index}. Ending.")
                break

            chunk_key = f"{STAGING_PREFIX}chunk_{start_index}.xml"
            if upload_chunk_to_s3(content, chunk_key):
                successful_chunks.append(f"chunk_{start_index}.xml")
            else:
                failed_chunks.append(start_index)

            if content.count("<entry>") < CHUNK_SIZE:
                logger.info(f"Last chunk reached at index {start_index}.")
                break

            start_index += CHUNK_SIZE
        except Exception as e:
            logger.error(f"[{start_index}] Fatal error: {e}")
            failed_chunks.append(start_index)
            break

    # Write manifest
    manifest = write_manifest(successful_chunks, failed_chunks)

    if manifest["status"] == "SUCCESS":
        if latest_manifest_successful():
            backup_folder = f"raw/backup/{RUN_DATE}/"
            copy_folder(f"raw/latest/{RUN_DATE}/", backup_folder)

        copy_folder(STAGING_PREFIX, f"raw/latest/{RUN_DATE}/")
        logger.info("Staging promoted to latest.")
    else:
        logger.error("Data collection failed. Check logs and manifest.")
        # TODO: Add CloudWatch/SNS alert trigger here
