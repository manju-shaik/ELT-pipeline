{{ config(
    materialized = "table",
    partition_by = {
        "field": "transaction_date",
        "data_type": "date"
    },
    cluster_by = ["customer_id"]
) }}

SELECT
    transaction_id,
    customer_id,
    amount,
    currency,
    transaction_date
FROM
    silent-region-463011-h9.example.stg_transaction_external
WHERE
    customer_id IS NOT NULL
