# README: Customer & Transactions Data Pipeline on GCP

## Architecture Overview

This project implements a scalable ELT data pipeline on Google Cloud Platform (GCP) to simulate ingesting customer and transaction data for analytics.

### Technologies Used:

* Google Cloud Storage (GCS) – raw and cleaned data storage
* Cloud Composer (Airflow) – workflow orchestration
* Google BigQuery – external and final analytical tables
* dbt (Data Build Tool) – SQL transformations and modeling
* Python (Pandas) – file cleaning logic

### Data Flow:

1. CSVs (customers.csv, transactions.csv) are uploaded to GCS under a `raw/` path.
2. Airflow reads the raw files, cleans them using Pandas, and saves cleaned versions to a `cleaned/` path in GCS.
3. dbt macros are triggered via `run-operation` to create external tables in BigQuery from the cleaned CSVs.
4. dbt models run and materialize final tables into BigQuery using partitioning and clustering.

## Setup Instructions

### Prerequisites

* A GCP Project with billing enabled
* gcloud CLI and service account key file with required permissions
* A Cloud Composer environment with dbt installed

### GCP IAM Roles Required (Minimal)

- storage.objectAdmin (or objectViewer + objectCreator)
- bigquery.dataEditor
- bigquery.jobUser
- composer.worker
- composer.environmentAndStorageObjectViewer


### GCS Bucket Layout

The structure used for organizing files in the bucket is as follows:

* `gs://firstdfbkt/dataflowbkt/customers.csv` – raw customer data
* `gs://firstdfbkt/dataflowbkt/transactions.csv` – raw transaction data
* `gs://firstdfbkt/cleaned/customer_cleaned.csv` – cleaned customer data
* `gs://firstdfbkt/cleaned/transaction_cleaned.csv` – cleaned transaction data

### Airflow DAG: Combined Data Cleaning and dbt Execution

DAG ID: `gcs_dbt_pipeline_combined`

Steps:

1. Clean customers.csv → cleaned/customer\_cleaned.csv
2. Clean transactions.csv → cleaned/transaction\_cleaned.csv
3. dbt debug
4. dbt run-operation create\_external\_customers
5. dbt run-operation create\_external\_transaction
6. dbt run --select final\_customers

### How to Deploy

1. Upload the DAG file to Composer's DAGs folder
2. Upload the dbt project to `/home/airflow/gcs/data/dbt-project` in Composer
3. Trigger the DAG manually from Composer or via API

### How to Verify

Check BigQuery for:

* Dataset: example (or interview\_task\_us)
* Tables:

  * stg\_customers\_external2 (external table)
  * final\_customers (materialized table)

## Assumptions

* Input CSVs have valid headers like customer\_id, transaction\_date
* joined\_date and transaction\_date can be parsed as DATE
* GCS bucket and BigQuery dataset are in the same region (US)
* The service account has read access to GCS and write access to BigQuery
* File schema remains consistent between uploads

## Future Improvements

### Functional

* Add schema validation and tests using dbt or Great Expectations
* Support additional file formats like Parquet or JSON
* Incorporate dbt test and docs generation in the DAG
* Build more models: customer\_monthly\_spend, top\_lifetime\_value\_customers

### Infrastructure

* Automate GCS and BigQuery setup using Terraform
* Add GitHub Actions for CI (dbt run, dbt test)
* Configure DAG for scheduled runs (e.g., daily)
* Add alerts or notifications for DAG failures or successes
