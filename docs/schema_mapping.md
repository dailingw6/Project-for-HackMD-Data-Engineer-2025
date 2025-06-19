#  Schema Mapping: arXiv Metadata to Tables

This guide maps raw XML/JSON fields from arXiv into the normalized tables produced by the Glue ETL job.

---

##  Paper Table (`paper`)
| Column       | Source Field        | Notes                        |
|--------------|---------------------|------------------------------|
| paper_id     | `entry.id`          | Full arXiv ID URL            |
| title        | `entry.title`       | Plaintext title              |
| summary      | `entry.summary`     | Abstract                     |
| published    | `entry.published`   | ISO timestamp                |
| updated      | `entry.updated`     | ISO timestamp                |
| journal_ref  | `entry.journal_ref` | Optional                     |
| comment      | `entry.comment`     | Optional                     |
| doi          | `entry.doi`         | Optional                     |
| primary_category | `entry.primary_category.term` | Used for default category |

---

##  Contributor Table (`contributor`)
| Column        | Source Field                | Notes                       |
|---------------|-----------------------------|-----------------------------|
| contributor_id| Auto-generated              | Surrogate key              |
| name          | `author.name`               |                             |
| affiliation   | `author.affiliation`        | May be null                |

---

##  Paper_Contributor Table (`paper_contributor`)
| Column        | Source Field         | Notes                          |
|---------------|----------------------|---------------------------------|
| paper_id      | from paper           | Foreign key                    |
| contributor_id| from contributor     | Foreign key                    |
| role          | `submitter` or `author` | Simplified person-role mapping |
| author_order  | In author array      | Preserves order                |

---

##  Category Table (`category`)
| Column       | Source Field      | Notes             |
|--------------|-------------------|-------------------|
| category_id  | Auto-generated    |                   |
| category_name| `entry.category`  | Term attribute    |

---

##  Paper_Category Table (`paper_category`)
| Column       | Source Field      | Notes                     |
|--------------|-------------------|---------------------------|
| paper_id     | from paper        | FK                        |
| category_id  | from category     | FK                        |

---

##  Paper_Submission Table (`paper_submission`)
| Column       | Source Field            | Notes                  |
|--------------|-------------------------|------------------------|
| paper_id     | from paper              |                        |
| version      | `entry.version`         | Requires parsing       |
| updated      | `entry.updated`         | Timestamp              |
| submitter    | `entry.submitter`       | Not always available   |

---

##  Notes
- All relational links are based on surrogate keys or arXiv IDs
- One paper → many authors, categories, and versions



