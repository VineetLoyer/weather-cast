FROM apache/airflow:2.5.0-python3.7

USER root

# Install additional system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories and set permissions
RUN mkdir -p /opt/airflow/dataset/raw /opt/airflow/dataset/processed && \
    chown -R airflow:root /opt/airflow && \
    chmod -R 775 /opt/airflow

# Switch to airflow user for pip installations
USER airflow

# Install Python packages
COPY --chown=airflow:root requirements.txt /requirements.txt
RUN pip install --user --no-cache-dir -r /requirements.txt

WORKDIR /opt/airflow