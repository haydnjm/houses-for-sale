from datetime import timedelta, datetime
from dotenv import load_dotenv
import os

load_dotenv()

gcp_project = os.getenv("GCP_PROJECT")
bq_dataset = os.getenv("BQ_DATASET")
bq_table = os.getenv("BQ_TABLE")


def write_to_bigquery(client, rows):
    print(f"Attempting to write {len(rows)} rows to BigQuery")
    # Big query table Id
    table_id = f"{gcp_project}.{bq_dataset}.{bq_table}"

    for row in rows:
        # Check if row already exists in BigQuery
        # If the house was added more than 7 days ago, re-add it
        buffer = datetime.fromisoformat(row["inserted_date"]) - timedelta(days=7)
        query = f'SELECT * FROM `{table_id}` where id="{row["id"]}" and inserted_date > TIMESTAMP("{buffer}") LIMIT 1'

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
