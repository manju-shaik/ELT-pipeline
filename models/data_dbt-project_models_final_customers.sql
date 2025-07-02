{{ config(
    materialized = "table",
    partition_by = {
        "field": "customer_id",
        "data_type": "integer"
    },
    cluster_by = ["customer_id"]
) }}

select
    customer_id,
    first_name,
    last_name,
    email,
    signup_date
from silent-region-463011-h9.example.stg_customers_external5
where customer_id is not null