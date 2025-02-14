# Weather-Cast

A comprehensive data engineering project that implements an end-to-end ETL pipeline for weather data, incorporating data collection, storage, transformation, and visualization.

> Deployed at: [https://weather-cast.streamlit.app/](https://weather-cast.streamlit.app/)

### 1. **Data Ingestion**

* **Source** :  [OpenWeatherMap]() API.
* **Tools** :
  * Python scripts for API calls (`requests`, `airflow` operators).
* **Frequency** : 15-min intervals via Airflow DAG
* **Metrics :** Temperature, Pressure, Humidity, Wind Speed, Cloud Cover

---

### 2. **Storage Layer**

* **Raw Data Storage** :
  * **-****Local Storage******: JSON files organized by city and timestamp
  * **-****Cloud Storage******: AWS S3 bucket with hierarchical structure
* ```
  s3://bucket-name/
       └── raw/
           ├── Los_Angeles/
           │   └── YYYY-MM-DD/
           │       └── HH-MM.json
           └── New_York/
               └── YYYY-MM-DD/
                   └── HH-MM.json


  ```
* **Processed Data Storage:**
  * AWS(PostgreSQL) for transformed data storage and fast retrieval.
  * Schema Structure -
    ```
    weather_data (
             id SERIAL PRIMARY KEY,
             location VARCHAR(255),
             temperature FLOAT,
             pressure FLOAT,
             humidity FLOAT,
             wind_speed FLOAT,
             cloud_cover INT,
             date DATE,
             time TIME,
             created_at TIMESTAMP
         )
    ```
* **Data Lake** :
  * S3 as data lake for storing backup.

---

### 3. **ETL Pipeline**

* **1.****Extract******

  - Fetch real-time weather data from OpenWeather API
  - Data validation and error handling
  - Raw data persistence in both local and S3 storage
* **2.****Transform******
  **-** Temperature conversion (Kelvin to Celsius)
  **-** Data standardization
  **-** Timestamp processing
  **-** Data quality checks
* **3.****Load******
  **-** Incremental loading to RDS
  **-** Duplicate handling
  **-** Data integrity validation

---

### 4.Orchestration

* **Tools** : Apache Airflow for orchestrating ETL workflows.
* **Workflow** :
  * create_table >> fetch_weather_data >> [local storage, upload_to_s3, insert_into_rds] >> [store processed data in S3(backup)]

---

### 6. **Data Visualization**

**
    Framework**: Streamlit

**
    Features**:

    - Real-time metrics display

    - Historical trend analysis

    - Interactive time-series plots

    - Theme customization

---

Version 2.0 - Currenly working on

### 7. **Machine Learning**

* Using LSTM to forecast for next 30 days (integration left, training and tuning done)
* Orchestration  - updating the next 30 days automatically, adding to existing Airflow DAG (remaining)

---



## Deployment

### Pipeline Deployment

```bash
# Start Airflow services
docker-compose up -d

# Access Airflow UI
http://localhost:8080
```


### Dashboard Deployment

* Hosted on Streamlit Cloud
* Continuous deployment from GitHub repository
* Environment variables managed through Streamlit Secrets


## Monitoring & Maintenance

### Data Quality Checks

* Schema validation
* Data type verification
* Null value handling
* Duplicate detection

### Pipeline Monitoring

* Airflow task success rate
* Data freshness monitoring
* Error logging and alerting
* Performance metrics tracking
