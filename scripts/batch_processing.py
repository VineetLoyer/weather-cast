from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, to_date, round, expr
import os
import logging
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

# 🔹 Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BatchProcessing")

# 🔹 Ensure JAVA_HOME is set
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"

# 🔹 Initialize Spark Session
try:
    spark = SparkSession.builder \
        .appName("WeatherBatchProcessing") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.5.0") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .config("spark.ui.port", "4050") \
        .getOrCreate()

except Exception as e:
    logger.error(f"❌ Failed to initialize Spark Session: {e}")
    exit(1)

# 🔹 Constants
DATA_DIR = "/opt/airflow/data/"
KELVIN_TO_CELSIUS = 273.15

# 🔹 Function: Validate Temperature Data
def validate_temperature(df):
    if "temp" not in df.columns:
        logger.error("❌ Temperature column is missing! Skipping validation.")
        return df

    invalid_temps = df.filter((col("temp") < 200) | (col("temp") > 350)).count()
    if invalid_temps > 0:
        logger.warning(f"⚠️ Found {invalid_temps} invalid temperature records.")
        return df.filter((col("temp") >= 200) & (col("temp") <= 350))
    
    return df

# 🔹 Load and Process Data
try:
    # Find all JSON files recursively
    json_files = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    if not json_files:
        logger.error("❌ No data files found. Exiting...")
        exit(1)

    # Read JSON into DataFrame
    df = spark.read.option("multiline", "true").json(json_files)

    # Ensure required columns exist
    required_columns = ["name", "main.temp", "main.humidity", "wind.speed", "wind.deg", "clouds.all", "weather", "dt"]
    for col_name in required_columns:
        if col_name not in df.columns:
            logger.error(f"❌ Missing column: {col_name}. Skipping processing.")
            exit(1)

    # Extract first weather condition and description from array
    df = df.withColumn("weather_main", expr("weather[0].main")) \
           .withColumn("weather_description", expr("weather[0].description"))

    # Drop rows where 'name' is missing
    df = df.filter(col("name").isNotNull())

    # Validate and clean data
    df = validate_temperature(df)

    # Transform Data
    df = df.select(
        col("name").alias("location"),
        round(col("main.temp") - KELVIN_TO_CELSIUS, 2).alias("temperature_celsius"),
        col("main.humidity").alias("humidity"),
        col("wind.speed").alias("wind_speed"),
        col("wind.deg").alias("wind_direction"),
        col("clouds.all").alias("cloud_coverage"),
        col("weather_main").alias("weather_condition"),
        col("weather_description").alias("weather_description"),
        to_date(col("dt").cast("timestamp")).alias("date")
    )

    # Aggregate daily data
    daily_agg = df.groupBy("location", "date").agg(
        round(avg("temperature_celsius"), 2).alias("avg_temp"),
        round(avg("humidity"), 2).alias("avg_humidity"),
        round(avg("wind_speed"), 2).alias("avg_wind_speed"),
        round(avg("cloud_coverage"), 2).alias("avg_cloud_coverage"),
        count("*").alias("record_count")
    ).dropDuplicates(["location", "date"])

    # Ensure DB credentials are not empty
    if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS]):
        logger.error("❌ Database credentials are missing! Check your environment variables.")
        exit(1)

    # Save to PostgreSQL (RDS)
    daily_agg.write \
        .format("jdbc") \
        .option("url", f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}") \
        .option("dbtable", "weather_summary") \
        .option("user", DB_USER) \
        .option("password", DB_PASS) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

    logger.info("✅ Batch processing completed successfully.")

except Exception as e:
    logger.error(f"❌ Batch processing failed: {e}")
    exit(1)

finally:
    spark.stop()
