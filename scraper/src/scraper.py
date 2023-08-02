from google.cloud import bigquery
import os
from dotenv import load_dotenv
from funda import scrape_funda
from pararius import scrape_pararius
import json

load_dotenv()

gcp_project = os.getenv("GCP_PROJECT")
service_account_path = os.getenv("SERVICE_ACCOUNT_PATH")
bq_dataset = os.getenv("BQ_DATASET")
bq_table = os.getenv("BQ_TABLE")
env = os.getenv("ENV")

print("ENV: ", env, gcp_project, service_account_path, bq_dataset, bq_table)

# Set up BigQuery client

client = (
    bigquery.Client.from_service_account_json(
        f"{os.path.dirname(os.path.realpath(__file__))}/{service_account_path}"
    )
    if env == "dev"
    else bigquery.Client()
)


def write_to_bigquery(rows):
    print(f"Attempting to write {len(rows)} rows to BigQuery")
    # Big query table Id
    table_id = f"{gcp_project}.{bq_dataset}.{bq_table}"

    for row in rows:
        # Check if row already exists in BigQuery
        query = f'SELECT * FROM `{table_id}` where id="{row["id"]}" and inserted_date LIMIT 1'
        results = client.query(query).result()
        results_list = list(results)

        if len(results_list) == 0:
            # Insert the rows into BigQuery table
            errors = client.insert_rows_json(
                table_id,
                [row],
            )

            if errors:
                print(f"Encountered errors while inserting {row.id}: {errors}")
            else:
                print(f"Successfully inserted {row['id']}")
        else:
            print(f"Row with id {row['id']} already exists in BigQuery.")


# Scrape funda houses
funda_houses = scrape_funda(
    os.getenv("ENV"), os.getenv("FUNDA_BASE_URL"), os.getenv("FUNDA_SEARCH_URL")
)

write_to_bigquery(funda_houses)

# Scrape Pararius houses
pararius_houses = scrape_pararius(
    os.getenv("ENV"),
    os.getenv("PARARIUS_BASE_URL"),
    os.getenv("PARARIUS_SEARCH_URL"),
)

print(json.dumps(pararius_houses, indent=4))

# Write the funda_houses to BigQuery
write_to_bigquery(pararius_houses)
