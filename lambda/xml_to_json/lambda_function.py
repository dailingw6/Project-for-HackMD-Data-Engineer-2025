import boto3
import xml.etree.ElementTree as ET
import os
import logging
import json
from datetime import datetime
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

# Environment variables
PARSED_PREFIX = os.environ.get("PARSED_PREFIX", "parsed/")
TARGET_BUCKET = os.environ.get("TARGET_BUCKET", "arxiv-raw-data-bucket")
LATEST_PREFIX = os.environ.get("LATEST_PREFIX", "raw/latest/")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 5))

# Parse XML into list of structured records
def parse_entries(xml_content):
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    root = ET.fromstring(xml_content)
    entries = []

    for entry in root.findall('atom:entry', ns):
        parsed_entry = {
            "id": entry.findtext('atom:id', default='', namespaces=ns),
            "title": entry.findtext('atom:title', default='', namespaces=ns).strip(),
            "summary": entry.findtext('atom:summary', default='', namespaces=ns).strip(),
            "published": entry.findtext('atom:published', default='', namespaces=ns),
            "updated": entry.findtext('atom:updated', default='', namespaces=ns),
            "doi": entry.findtext('arxiv:doi', default='', namespaces=ns),
            "primary_category": entry.find('arxiv:primary_category', ns).attrib.get('term', '') if entry.find('arxiv:primary_category', ns) is not None else '',
            "journal_ref": entry.findtext('arxiv:journal_ref', default='', namespaces=ns),
            "comment": entry.findtext('arxiv:comment', default='', namespaces=ns),
            "authors": [],
            "affiliations": [],
            "categories": []
        }

        for author in entry.findall('atom:author', ns):
            name = author.findtext('atom:name', default='', namespaces=ns)
            affil = author.findtext('arxiv:affiliation', default='', namespaces=ns)
            if name:
                parsed_entry['authors'].append(name)
            if affil:
                parsed_entry['affiliations'].append(affil)

        for category in entry.findall('atom:category', ns):
            term = category.attrib.get('term')
            if term:
                parsed_entry['categories'].append(term)

        entries.append(parsed_entry)

    return entries

def list_latest_xml_files():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    prefix = f"{LATEST_PREFIX}{today}/"
    paginator = s3.get_paginator('list_objects_v2')
    objects = []
    for page in paginator.paginate(Bucket=TARGET_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj['Key'].endswith(".xml"):
                objects.append(obj['Key'])
    return objects[:BATCH_SIZE]

def process_xml_file(src_key):
    logger.info(f"Processing file: s3://{TARGET_BUCKET}/{src_key}")
    try:
        response = s3.get_object(Bucket=TARGET_BUCKET, Key=src_key)
        xml_data = response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read S3 object: {e}")
        return False

    try:
        parsed_entries = parse_entries(xml_data)
        logger.info(f"Extracted {len(parsed_entries)} entries from XML")
    except Exception as e:
        logger.error(f"Failed to parse XML: {e}")
        return False

    try:
        buffer = BytesIO()
        for entry in parsed_entries:
            buffer.write(json.dumps(entry).encode('utf-8'))
            buffer.write(b'\n')
        buffer.seek(0)

        base_filename = src_key.split("/")[-1].replace(".xml", ".jsonl")
        today = datetime.utcnow().strftime('%Y-%m-%d')
        output_key = f"{PARSED_PREFIX}{today}/{base_filename}"

        s3.put_object(Bucket=TARGET_BUCKET, Key=output_key, Body=buffer.getvalue())
        logger.info(f"✅ Saved JSON Lines to s3://{TARGET_BUCKET}/{output_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON Lines to S3: {e}")
        return False

def lambda_handler(event, context):
    logger.info("Starting XML-to-JSON-Lines transformation batch run...")

    xml_files = list_latest_xml_files()
    logger.info(f"Found {len(xml_files)} XML files to process.")

    success = 0
    fail = 0

    for key in xml_files:
        if process_xml_file(key):
            success += 1
        else:
            fail += 1

    logger.info(f"✅ Finished. Success: {success}, Failures: {fail}")