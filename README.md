# Project-for-HackMD-Data-Engineer-2025

## Overview
This project implements a reusable, scalable, and observable data pipeline to collect, process, and store metadata from the arXiv API. The system is designed to support downstream use cases such as academic dashboards, institutional rankings, and paper recommendation engines. It leverages AWS Lambda, S3, DynamoDB, and CloudWatch to ensure modularity and performance while adhering to modern data engineering best practices.

## Architecture & Design Rationale
System Architecture Highlights:
Data Collection: A Lambda function periodically queries the arXiv API, processes the metadata in JSON format, and stores raw records in S3 and structured records in DynamoDB.

Data Modeling: DynamoDB tables follow a relational-style design, separating paper, category, and paper_category for join-like flexibility without compromising NoSQL performance.

Observability: CloudWatch logs, custom metrics, and alarms monitor Lambda executions, error counts, and API response anomalies.

Configurability: Parameters such as search_query, start, and max_results are externalized to support flexible ingestion strategies across disciplines or topics.

Rationale for Design:
Separation of raw and structured layers (S3 vs. DynamoDB) allows both machine learning and analytical users to access data in formats suited to their needs.

Use of JSON aligns with arXiv's API structure and simplifies parsing; this is more efficient than handling large zipped XML datasets.

Category normalization supports many-to-many relationships, enabling downstream co-authorship graphs and multi-disciplinary queries.

## Performance and Scalability Considerations
Lambda Streaming to S3: JSON is streamed directly to S3, avoiding memory-intensive operations (especially useful when working with high-volume queries).

Chunked API Pagination: ArXiv's paginated API is handled in a loop with backoff and checkpointing logic to safely resume ingestion.

DynamoDB Table Design:

Keys are designed for high-cardinality partitions (e.g., paper_id, category_id) to avoid hot partitions.

Avoided deep nested writes or large single-item payloads to stay within DynamoDB’s 400KB per item limit.

## Data Quality & Anomaly Handling
Challenges Encountered:
Multiple Categories per Paper: ArXiv papers can have multiple primary and secondary categories, requiring careful deduplication and linkage logic.

Non-standard Characters: Abstracts and titles sometimes contain LaTeX or unicode artifacts; cleaned or escaped during JSON processing.

Unstable API behavior: The API occasionally returns malformed entries or rate-limits during high-frequency access.

Safeguards Implemented:
Validation rules for paper_id, title, and updated_date ensure schema consistency before storage.

Retry with exponential backoff handles intermittent API failures.

Deduplication logic avoids re-processing papers with unchanged updated_date.

## Fault Tolerance and Recovery
Idempotent Writes: Upserts are used in DynamoDB to allow safe re-runs without data duplication.

Checkpointing: Each Lambda run logs its last successful start offset and timestamp, enabling resumable jobs.

CloudWatch Alarms: Triggers alerting for:

Lambda timeout or failure

Unusually high error rate

Drop in the number of records ingested

## Assumptions
Paper ID is globally unique and can be used as the primary key for both raw and structured storage.

Categories are relatively stable, i.e., arXiv rarely renames or deprecates them. If they do, the system should be re-run from scratch for affected disciplines.

Downstream teams (analysts, data scientists) prefer JSON for flexibility and DynamoDB tables for structured queries via Athena or ETL exports.

Title and abstract fields are sufficient for initial ML-based recommendation prototypes—no full-text parsing is included in this phase.

## Future Extensions
Scheduled retraining for NLP-based paper vectorization on S3-stored JSON.

ETL to Redshift or Athena for large-scale SQL querying.

DynamoDB-to-OpenSearch sync for text-based relevance search on arXiv abstracts.

Real-time pipeline triggers for newly published papers, using EventBridge or SNS.

