{% macro create_external_transaction() %}
  {% set sql %}
    create or replace external table silent-region-463011-h9.example.stg_transaction_external
    options (
      format = 'CSV',
      uris = ['gs://firstdfbkt/cleaned/transaction_cleaned.csv'],
      skip_leading_rows = 1
    )
  {% endset %}

  {% do run_query(sql) %}
{% endmacro %}