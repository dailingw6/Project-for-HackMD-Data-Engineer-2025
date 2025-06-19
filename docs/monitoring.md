#  Monitoring & Observability

This guide outlines how to monitor and track the health of each pipeline component across Lambda, S3, and Glue.

---

##  Key Monitoring Goals
- Detect failed Lambda runs or incomplete manifest
- Track data completeness (missing chunks, empty files)
- Alert on parsing or transformation errors
- Ensure end-to-end flow completion

---

##  Lambda: APItoXML

###  Logs
- View in: **CloudWatch → Log Groups → /aws/lambda/OAIHarvesterLambda**
- Key events:
  - Start and end of each run
  - Resumption token progress
  - Retry and timeout logs
  - Manifest written with status = SUCCESS/FAILED

###  Metrics
Enable via CloudWatch:
- `Invocations`
- `Errors`
- `Duration`
- Custom: `manifest.status == FAILED`

###  Alerts
Set CloudWatch Alarm:
- `Errors > 0` within 5-minute period
- `manifest.status` logged as FAILED (via pattern filter)

---

##  Lambda: XMLtoJSON

###  Logs
- View in: **/aws/lambda/XMLtoJSONLambda**
- Per-file success/failure logs
- Count of parsed entries per XML

###  Metrics
- `Invocations`
- `Errors`
- Custom: empty JSON (0 entries)

---

##  Glue ETL Job

###  Logs
- Glue Console → Jobs → `GLUEETLJob` → Runs
- Log Group: `/aws-glue/jobs/output`

###  Metrics
- Job Success/Fail status
- # of records written per table
- Job duration

###  Alerts
- CloudWatch alarm on failed Glue job
```json
{ $.jobRunState = "FAILED" }
```
- Optionally: SNS topic to notify team

---

## 📂 S3 Manifest Inspection

Each `raw/latest/{run_date}/manifest.json` includes:
```json
{
  "run_id": "2025-06-19",
  "status": "SUCCESS",
  "successful_chunks": 47,
  "failed_chunks": 0
}
```
Use this to:
- Automatically promote `latest` → `backup`
- Block Glue job if status is not `SUCCESS`

---

##  Common Failure Cases
| Stage | Issue | Resolution |
|-------|-------|------------|
| API | Resumption token lost | Retry with saved token (S3) |
| API | Timeout | Increase Lambda timeout to 5–10 mins |
| XML | Parse error | Log offending file + skip |
| Glue | Field mismatch | Validate schema + reprocess |

---

##  Monitoring Dashboard Proposal

###  Overview
I propose building a centralized monitoring dashboard to visualize the health and status of the pipeline using Amazon CloudWatch + QuickSight or Grafana.

###  Components Tracked
| Stage         | Metrics                                 |
|---------------|------------------------------------------|
| APItoXML      | Invocation count, error count, duration, manifest status |
| XMLtoJSON     | Parse errors, empty entry detection      |
| Glue ETL      | Job status, duration, record count       |
| Manifest File | # of failed/successful chunks            |

###  Dashboard Implementation Options
| Option               | Tools                  | Notes                          |
|----------------------|------------------------|-------------------------------|
| **CloudWatch**       | Native AWS             | Simple, no extra infra needed |
| **QuickSight**       | S3 + Athena            | Rich visuals, joins manifest  |
| **Grafana**          | CloudWatch plugin      | Visual + alerting flexibility |


