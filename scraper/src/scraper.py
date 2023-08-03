from google.cloud import bigquery
import os
from dotenv import load_dotenv
from funda import scrape_funda
from pararius import scrape_pararius
from data.write_to_big_query import write_to_bigquery

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

# Scrape funda houses
funda_houses = scrape_funda(
    os.getenv("ENV"), os.getenv("FUNDA_BASE_URL"), os.getenv("FUNDA_SEARCH_URL")
)

write_to_bigquery(client, funda_houses)

# Scrape Pararius houses
pararius_houses = scrape_pararius(
    os.getenv("ENV"),
    os.getenv("PARARIUS_BASE_URL"),
    os.getenv("PARARIUS_SEARCH_URL"),
)

# Write the funda_houses to BigQuery
write_to_bigquery(client, pararius_houses)
