{% macro create_external_customers() %}
  {% set sql %}
    create or replace external table silent-region-463011-h9.example.stg_customers_external5
    options (
      format = 'CSV',
      uris = ['gs://firstdfbkt/cleaned/customer_cleaned.csv'],
      skip_leading_rows = 1
    )
  {% endset %}

  {% do run_query(sql) %}
{% endmacro %}