#  Architecture Overview

##  Goal

To build a resilient, modular, and scalable data pipeline that supports academic metadata ingestion, transformation, and storage using arXiv’s OAI-PMH feed.

---

##  High-Level Data Flow

```
[ EventBridge Schedule ]
        ↓
[ Lambda: APItoXML ]
        ↓
[ S3: raw/latest/YYYY-MM-DD/ ]
        ↓ (S3 trigger)
[ Lambda: XMLtoJSON ]
        ↓
[ S3: parsed/YYYY-MM-DD/ ]
        ↓ (manual or conditional trigger)
[ Glue Job: GLUEETL ]
        ↓
[ S3: tables/ ]  →  [ Athena / Dashboard ]
```

---

##  S3 Folder Structure

```
s3://arxiv-raw-data-bucket/
├── raw/
│   ├── latest/
│   │   └── 2025-06-19/
│   │       └── part_0.xml
│   └── backup/
│       └── 2025-06-18/
├── parsed/
│   └── 2025-06-19/
│       └── part_0.jsonl
└── tables/
    ├── paper/
    ├── contributor/
    ├── paper_contributor/
    ├── category/
    ├── paper_category/
    └── paper_submission/
```

---

##  Pipeline Components

###  1. `APItoXML` Lambda

* Fetches OAI-PMH records in chunks (resumption token based)
* Writes XML parts to S3 `raw/latest/{run_date}/`
* Includes manifest, status flag, and backup rotation

###  2. `XMLtoJSON` Lambda

* Triggered per XML file created
* Parses full arXiv metadata fields
* Outputs newline-delimited JSON (`.jsonl`)

###  3. `GlueETL` Job

* Reads from `parsed/{run_date}/`
* Transforms into 6 normalized tables
* Writes output to `tables/` in Parquet format

---

##  Design Considerations

* **Traceability:** Every stage includes logging and manifest tracking
* **Observability:** Failures are captured in manifest + CloudWatch alerts (optional)
* **Parallelism:** Both XML parsing and Glue transformations are parallelizable
* **Fault-tolerant:** Retries, fallbacks, and stage-specific backup mechanisms

---

##  Example Trigger Timeline

* `APItoXML`: Every 5 minutes via CloudWatch Rule
* `XMLtoJSON`: Instantly on S3 upload
* `GLUEETL`: Periodically (or based on manifest success)

---

##  Future Extensions

* OpenSearch indexing for full-text search
* SageMaker for recommendation system
* NLP-based vectorization of abstract/title
* External enrichment (DOI, citation, CORE ranking)


