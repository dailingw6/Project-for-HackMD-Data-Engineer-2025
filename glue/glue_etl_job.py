import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import explode, col, monotonically_increasing_id, posexplode_outer
from pyspark.sql.types import StringType, IntegerType

args = getResolvedOptions(sys.argv, ['RAW_S3_PATH', 'OUTPUT_S3_PATH'])

RAW_S3_PATH = args['RAW_S3_PATH']
OUTPUT_S3_PATH = args['OUTPUT_S3_PATH']

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Load raw JSON from parsed S3
raw_df = spark.read.json(RAW_S3_PATH)

# ===== paper table =====
papers_df = raw_df.select(
    col("id").alias("paper_id"),
    col("title"),
    col("summary").alias("abstract"),
    col("published").alias("journal_publication_date"),
    col("updated").alias("updated_date")
).dropDuplicates(["paper_id"])

# ===== contributor table =====
authors_df = raw_df.select(explode(col("authors")).alias("name")).distinct()
authors_df = authors_df.withColumn("contributor_id", monotonically_increasing_id())

# ===== contributor mapping =====
authors_exploded = raw_df.select(
    col("id").alias("paper_id"),
    posexplode_outer(col("authors")).alias("author_order", "name")
).dropna(subset=["name"])

paper_contributor_df = authors_exploded.join(
    authors_df, on="name", how="left"
).select(
    "paper_id", "contributor_id",
    col("author_order") + 1,  # to make it 1-indexed
).withColumnRenamed("(author_order + 1)", "author_order")
paper_contributor_df = paper_contributor_df.withColumn("role", col("role").cast(StringType())).fillna({"role": "author"})

# ===== category table =====
exploded_cat = raw_df.select(explode(col("categories")).alias("category_code"))
category_df = exploded_cat.distinct().withColumn("category_id", monotonically_increasing_id())

# ===== paper_category =====
paper_category_df = raw_df.select(
    col("id").alias("paper_id"), explode(col("categories")).alias("category_code")
).join(
    category_df, on="category_code", how="left"
).select("paper_id", "category_id")

# ===== paper_submission =====
submission_df = raw_df.select(
    col("id").alias("paper_id"),
    col("published").alias("submission_date")
).withColumn("version", col("version").cast(IntegerType()))

# ===== Write tables to S3 as Parquet =====
papers_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/paper")
authors_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/contributor")
paper_contributor_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/paper_contributor")
category_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/category")
paper_category_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/paper_category")
submission_df.write.mode("overwrite").parquet(f"{OUTPUT_S3_PATH}/paper_submission")
